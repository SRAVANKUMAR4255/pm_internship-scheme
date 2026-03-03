import os
import re
import warnings
import numpy as np
import logging

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_models')

_model      = None
_tfidf      = None
_le         = None
_df_jobs    = None
_job_matrix = None
_models_loaded = False
_load_error    = None


def _load_models():
    global _model, _tfidf, _le, _df_jobs, _job_matrix, _models_loaded, _load_error
    if _models_loaded:
        return True
    try:
        import joblib
        import pandas as pd
        _model   = joblib.load(os.path.join(MODEL_DIR, 'best_model.pkl'))
        _tfidf   = joblib.load(os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
        _le      = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
        _df_jobs = pd.read_pickle(os.path.join(MODEL_DIR, 'df_jobs.pkl'))
        _job_matrix = None
        _models_loaded = True
        logger.info(f'Models loaded: {type(_model).__name__}, '
                    f'{len(_le.classes_)} categories, {len(_df_jobs)} jobs')
        return True
    except Exception as e:
        _load_error = str(e)
        logger.warning(f'ML models not available: {e}')
        return False


def models_available():
    return _load_models()


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ''
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + ' '
        if text.strip():
            return text.strip()
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + ' '
        doc.close()
        return text.strip()
    except Exception as e:
        raise RuntimeError(f'Could not read PDF: {e}')


def _get_nltk_tools():
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet',   quiet=True)
        nltk.download('omw-1.4',   quiet=True)
        return set(stopwords.words('english')), WordNetLemmatizer()
    except Exception:
        basic_stops = {'the','a','an','and','or','but','in','on','at','to',
                       'for','of','with','by','from','is','was','are','were',
                       'be','been','being','have','has','had','do','does','did',
                       'will','would','could','should','may','might','shall',
                       'not','no','nor','so','yet','both','either','neither',
                       'this','that','these','those','i','me','my','we','our',
                       'you','your','he','his','she','her','it','its','they','their'}
        return basic_stops, None


def preprocess_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ''
    stop_words, lemmatizer = _get_nltk_tools()
    text = text.lower()
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [t for t in text.split() if t not in stop_words and len(t) > 2]
    if lemmatizer:
        try:
            tokens = [lemmatizer.lemmatize(t) for t in tokens]
        except Exception:
            pass
    return ' '.join(tokens)


def run_prediction(pdf_path: str) -> dict:
    """
    Returns a result dict that mirrors the Jupyter notebook output exactly:
    - words_raw, words_clean
    - clean_preview (first 200 chars)
    - predicted_category
    - confidence_score  (0–100 float)
    - top3_categories   [ {category, score, bar_filled, bar_empty} ]
    - top5_jobs         [ {rank, job_id, job_title, category, location, similarity_score} ]
    - ml_used
    """
    # ── Extract ───────────────────────────────────────────────────────────────
    raw_text   = extract_text_from_pdf(pdf_path)
    clean_text = preprocess_text(raw_text)

    if not clean_text.strip():
        raise ValueError(
            'No readable text found in this PDF. '
            'Please use a text-based (non-scanned) PDF.'
        )

    words_raw   = len(raw_text.split())
    words_clean = len(clean_text.split())
    preview     = clean_text[:200]

    result = {
        'words_raw':          words_raw,
        'words_clean':        words_clean,
        'clean_preview':      preview,
        'predicted_category': 'UNKNOWN',
        'confidence_score':   None,
        'top3_categories':    [],
        'top5_jobs':          [],
        'matched_internships': [],
        'raw_text_preview':   preview,
        'words_extracted':    words_raw,
        'ml_used':            False,
    }

    if not _load_models():
        # Keyword fallback
        cat = _keyword_fallback(clean_text)
        result['predicted_category'] = cat
        result['top3_categories'] = [
            {'category': cat, 'score': 100.0, 'bar_filled': 20, 'bar_empty': 0}
        ]
        return result

    try:
        from scipy.sparse import csr_matrix
        from sklearn.metrics.pairwise import cosine_similarity

        resume_vec     = _tfidf.transform([clean_text])
        resume_vec_abs = csr_matrix(resume_vec.copy())
        resume_vec_abs.data = np.abs(resume_vec_abs.data)

        # ── Category prediction ───────────────────────────────────────────────
        label_idx          = _model.predict(resume_vec_abs)[0]
        predicted_category = _le.inverse_transform([label_idx])[0]
        result['predicted_category'] = predicted_category

        # ── Confidence + Top 3 ────────────────────────────────────────────────
        top3_categories = []
        confidence      = None

        if hasattr(_model, 'predict_proba'):
            proba      = _model.predict_proba(resume_vec_abs)[0]
            confidence = float(proba.max()) * 100
            top3_idx   = np.argsort(proba)[::-1][:3]
            for idx in top3_idx:
                pct        = round(float(proba[idx]) * 100, 2)
                filled     = int(pct / 5)          # out of 20 blocks
                empty      = 20 - filled
                top3_categories.append({
                    'category':   _le.inverse_transform([idx])[0],
                    'score':      pct,
                    'bar_filled': filled,
                    'bar_empty':  empty,
                })

        elif hasattr(_model, 'decision_function'):
            scores         = _model.decision_function(resume_vec)[0]
            scores_shifted = scores - scores.min()
            norm_scores    = scores_shifted / (scores_shifted.sum() + 1e-9)
            confidence     = float(norm_scores.max()) * 100
            top3_idx       = np.argsort(norm_scores)[::-1][:3]
            for idx in top3_idx:
                pct    = round(float(norm_scores[idx]) * 100, 2)
                filled = int(pct / 5)
                empty  = 20 - filled
                top3_categories.append({
                    'category':   _le.inverse_transform([idx])[0],
                    'score':      pct,
                    'bar_filled': filled,
                    'bar_empty':  empty,
                })

        result['confidence_score']  = round(confidence, 2) if confidence else None
        result['top3_categories']   = top3_categories

        # ── Top 5 Jobs ────────────────────────────────────────────────────────
        global _job_matrix

        if _job_matrix is None:
            _job_matrix = _tfidf.transform(
                _df_jobs['clean_combined'].fillna('').replace('', ' ').tolist()
            )

        sim_scores = cosine_similarity(resume_vec, _job_matrix).flatten()
        top5_idx   = np.argsort(sim_scores)[::-1][:5]

        top5_jobs = []
        for rank, idx in enumerate(top5_idx, 1):
            row = _df_jobs.iloc[idx]
            top5_jobs.append({
                'rank':             rank,
                'job_id':           str(row.get('job_id', 'N/A')),
                'job_title':        str(row.get('job_title', 'N/A')),
                'category':         str(row.get('category', 'N/A')),
                'location':         str(row.get('location', 'N/A')),
                'similarity_score': round(float(sim_scores[idx]), 4),
            })

        result['top5_jobs'] = top5_jobs
        result['ml_used']   = True

    except Exception as e:
        logger.error(f'Prediction error: {e}')
        cat = _keyword_fallback(clean_text)
        result['predicted_category'] = cat
        result['top3_categories'] = [
            {'category': cat, 'score': 100.0, 'bar_filled': 20, 'bar_empty': 0}
        ]

    return result


def match_mentor_internships(predicted_category: str, clean_text: str = '') -> list:
    from mentor_portal.models import Internship

    SECTOR_MAP = {
        'technology':  ['technology','software','data','it','computer','web','programming','developer','python','java'],
        'finance':     ['finance','banking','accounting','fintech','investment','audit','tax'],
        'marketing':   ['marketing','sales','digital','seo','advertising','brand','customer'],
        'engineering': ['engineering','mechanical','electrical','civil','manufacturing','production'],
        'healthcare':  ['healthcare','medical','pharma','health','clinical','nursing'],
        'education':   ['education','teaching','training','learning','academic','coaching'],
        'legal':       ['legal','law','compliance','regulatory','litigation'],
        'design':      ['design','graphic','ui','ux','creative','figma','illustrator'],
        'logistics':   ['logistics','supply chain','operations','warehouse'],
        'agriculture': ['agriculture','farming','rural','agri'],
    }

    CATEGORY_TO_SECTOR = {
        'SALES':                  'marketing',
        'INFORMATION-TECHNOLOGY': 'technology',
        'DATA-SCIENCE':           'technology',
        'HR':                     'technology',
        'FINANCE':                'finance',
        'MARKETING':              'marketing',
        'ENGINEERING':            'engineering',
        'HEALTHCARE':             'healthcare',
        'EDUCATION':              'education',
        'LEGAL':                  'legal',
        'DESIGN':                 'design',
        'ACCOUNTANT':             'finance',
        'BUSINESS-DEVELOPMENT':   'marketing',
        'DIGITAL-MEDIA':          'marketing',
        'FITNESS':                'healthcare',
        'APPAREL':                'design',
        'AUTOMOBILE':             'engineering',
        'AVIATION':               'engineering',
        'BANKING':                'finance',
        'CHEF':                   'other',
        'CONSTRUCTION':           'engineering',
        'CONSULTANT':             'technology',
        'ARTS':                   'design',
        'ADVOCATE':               'legal',
        'BPO':                    'technology',
        'PUBLIC-RELATIONS':       'marketing',
        'TEACHER':                'education',
        'AGRICULTURE':            'agriculture',
        'ELECTRICAL-ENGINEERING': 'engineering',
        'MECHANICAL-ENGINEER':    'engineering',
        'NETWORK-SECURITY-ENGINEER': 'technology',
        'OPERATIONS-MANAGER':     'technology',
        'PMO':                    'technology',
    }

    matched = []
    try:
        internships   = Internship.objects.filter(is_active=True).select_related('mentor')
        cat_upper     = predicted_category.upper()
        text_lower    = clean_text.lower()
        mapped_sector = CATEGORY_TO_SECTOR.get(cat_upper, '')

        for internship in internships:
            score   = 0
            reasons = []

            sector_kws = SECTOR_MAP.get(internship.sector, [internship.sector.lower()])
            if internship.sector == mapped_sector:
                score += 40
                reasons.append(f'Category → Sector: {internship.get_sector_display()}')
            else:
                for kw in sector_kws:
                    if kw in text_lower:
                        score += 20
                        reasons.append(f'Keyword match: {kw}')
                        break

            if internship.skills_required:
                skills = [s.strip().lower() for s in internship.skills_required.split(',')]
                matched_skills = [s for s in skills if len(s) > 2 and s in text_lower]
                if matched_skills:
                    score += min(len(matched_skills) * 10, 40)
                    reasons.append(f'Skills: {", ".join(matched_skills[:3])}')

            title_words = [w for w in internship.title.lower().split() if len(w) > 3]
            for word in title_words:
                if word in text_lower:
                    score += 10
                    reasons.append(f'Title match: {word}')
                    break

            if score > 0:
                matched.append({
                    'id':              internship.id,
                    'title':           internship.title,
                    'company_name':    internship.company_name,
                    'sector':          internship.get_sector_display(),
                    'location':        internship.location,
                    'mode':            internship.get_mode_display(),
                    'stipend_amount':  internship.stipend_amount,
                    'duration':        internship.get_duration_display(),
                    'skills_required': internship.skills_required,
                    'mentor_name':     internship.mentor.full_name,
                    'match_score':     score,
                    'match_reasons':   list(dict.fromkeys(reasons)),
                })

        matched.sort(key=lambda x: x['match_score'], reverse=True)
        return matched[:5]

    except Exception as e:
        logger.error(f'Internship match error: {e}')
        return []


def _keyword_fallback(text: str) -> str:
    categories = {
        'INFORMATION-TECHNOLOGY': ['python','java','javascript','software','developer','web','database','sql','html','css','react','django'],
        'DATA-SCIENCE':           ['machine learning','data','analytics','tensorflow','pandas','numpy','sklearn','tableau','deep learning'],
        'FINANCE':                ['finance','accounting','financial','budget','investment','bank','tax','audit','revenue'],
        'SALES':                  ['sales','customer','retail','target','crm','negotiation','revenue','client','pipeline'],
        'MARKETING':              ['marketing','seo','social media','campaign','brand','digital','advertising','content'],
        'ENGINEERING':            ['engineering','mechanical','electrical','civil','cad','manufacturing','production','quality'],
        'HEALTHCARE':             ['medical','clinical','patient','hospital','healthcare','pharma','nursing','health'],
        'EDUCATION':              ['teaching','education','curriculum','student','academic','training','coaching'],
        'HR':                     ['recruitment','hiring','onboarding','payroll','hr','human resources','talent','employee'],
        'LEGAL':                  ['legal','law','contract','compliance','regulatory','litigation','attorney'],
        'DESIGN':                 ['design','creative','graphic','ui','ux','illustrator','photoshop','figma'],
    }
    text_lower = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in text_lower) for cat, kws in categories.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'GENERAL'