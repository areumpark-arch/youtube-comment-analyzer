#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 인사이트 분석기 v8.1
================================
v8.1 업데이트:
- 댓글 1000개 초과 시 분석/전체 댓글 수 표시
- 감성 분류 정확도 개선
- 의견 유형 카테고리 재정의
- UI 개선 (분석 기준 명시, 섹션 순서 변경)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import re
import io
from typing import List, Tuple, Dict, Optional
from collections import Counter, defaultdict
from datetime import datetime

# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 세션 상태
# =============================================================================
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .block-container { padding: 2rem 3rem !important; max-width: 1200px !important; }
    
    .header { text-align: center; padding: 2rem 0 1.5rem 0; }
    .header h1 { color: #1e3a5f; font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem 0; }
    .header p { color: #64748b; font-size: 1rem; margin: 0; }
    
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .video-info-box {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    .video-info-row {
        display: flex;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .video-info-row:last-child { border-bottom: none; }
    .video-info-label { color: #64748b; font-size: 0.85rem; min-width: 100px; font-weight: 500; }
    .video-info-value { color: #1e293b; font-size: 0.9rem; flex: 1; }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a5f;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .insight {
        background: white;
        border-left: 3px solid #1e3a5f;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .insight-title { font-weight: 600; color: #1e3a5f; font-size: 0.95rem; margin-bottom: 0.4rem; }
    .insight-desc { color: #475569; font-size: 0.9rem; line-height: 1.6; }
    .insight-action { color: #64748b; font-size: 0.85rem; font-style: italic; margin-top: 0.4rem; }
    
    .stat-box {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .stat-box-light {
        background: #f0f4f8;
        color: #1e3a5f;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .stat-value { font-size: 1.5rem; font-weight: 700; }
    .stat-label { font-size: 0.8rem; opacity: 0.9; }
    
    .lang-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
        background: #e2e8f0;
        color: #475569;
    }
    .lang-tag.primary { background: #1e3a5f; color: white; }
    
    .category-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-left: 4px solid #1e3a5f;
    }
    .category-title { font-weight: 600; color: #1e3a5f; font-size: 0.9rem; }
    .category-pct { color: #64748b; font-size: 0.85rem; }
    .category-sample { color: #475569; font-size: 0.85rem; font-style: italic; margin-top: 0.5rem; }
    
    .journey-stage {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .journey-awareness { background: #dbeafe; color: #1e40af; }
    .journey-interest { background: #dcfce7; color: #166534; }
    .journey-consideration { background: #fef3c7; color: #92400e; }
    .journey-intent { background: #fce7f3; color: #9d174d; }
    .journey-experience { background: #f3e8ff; color: #7c3aed; }
    
    .comment {
        background: #f8fafc;
        padding: 0.9rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #cbd5e1;
    }
    .comment.pos { border-color: #1e3a5f; }
    .comment.neg { border-color: #94a3b8; }
    .comment-text { color: #334155; font-size: 0.88rem; line-height: 1.5; }
    .comment-likes { color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem; }
    
    .warning-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background: #dbeafe;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .footer { text-align: center; padding: 2rem 0; color: #94a3b8; font-size: 0.8rem; }
    
    #MainMenu, footer, .stDeployButton {display: none;}
    
    .stButton > button {
        background: #1e3a5f;
        color: white;
        border: none;
        padding: 0.7rem 2rem;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button:hover { background: #2d5a87; }
    
    .stDownloadButton > button {
        background: white;
        color: #1e3a5f;
        border: 2px solid #1e3a5f;
    }
    .stDownloadButton > button:hover { background: #1e3a5f; color: white; }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        padding: 0.7rem 1rem;
    }
    
    [data-testid="stMetricValue"] { font-size: 1.5rem; color: #1e3a5f; }
    [data-testid="stMetricLabel"] { color: #64748b; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 설정 & 상수
# =============================================================================
CONFIG = {"max_comments": 1000, "top_keywords_count": 15}

STOPWORDS = set(['은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '도', '만', '로', '으로',
    '하고', '그리고', '그런데', '하지만', '그래서', '그러나', '또한', '및', '등', '더', '막', '좀', '이제',
    '나', '너', '우리', '저', '이것', '저것', '그것', '여기', '저기', '거기',
    '하다', '되다', '있다', '없다', '같다', '보다', '알다', '싶다', '주다', '보다',
    '하는', '하면', '해서', '했다', '한다', '할', '함', '되는', '되면', '됐다', '된다', '하게', '해요', '합니다',
    '있는', '있으면', '있고', '있어서', '있었다', '있을', '있음', '있어요', '있습니다',
    '것', '거', '수', '때', '중', '내', '년', '월', '일', '번', '분', '게', '데', '뭐', '왜', '어떻게',
    '영상', '댓글', '동영상', '유튜브', '채널', '구독', '좋아요', '시청', '진짜', '너무', '정말', '완전',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
    'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'and', 'but', 'or', 'so',
    'video', 'comment', 'youtube', 'channel', 'subscribe', 'like', 'just', 'really', 'very', 'much', 'what', 'how'])

POSITIVE_WORDS = {'좋다', '좋아', '좋네', '좋은', '좋았', '좋음', '좋아요', '좋습니다', '최고', '최고다', '최고야', '최고예요', '최고임',
    '대박', '대박이다', '멋지다', '멋져', '멋있다', '멋있어', '멋짐', '멋진', '예쁘다', '예뻐', '예쁨', '이쁘다', '이뻐', '예쁜',
    '사랑', '사랑해', '사랑해요', '사랑합니다', '감사', '감사해요', '감사합니다', '고마워', '고맙습니다',
    '행복', '행복해', '기쁘다', '즐겁다', '기대', '기대된다', '기대돼', '응원', '응원해', '화이팅', '파이팅', '힘내',
    '훌륭', '완벽', '감동', '설렘', '설레', '재밌', '재밌다', '재미있', '웃기다', '웃겨', '힐링', '귀엽', '귀여워', '귀여운', '귀염',
    '잘생', '잘생겼', '존잘', '존예', '짱', '쩔어', '쩐다', '미쳤', '미쳤다', '대단', '놀랍', '신기', '레전드',
    '인정', '추천', '갓', '존경', '천재', '아름답', '환상적', '역시', '믿고보는', '찐', '꿀잼', '핵잼', '존잼', '소름', '감탄', '공감',
    # v8.1 추가: 광고/모델 관련 긍정 표현
    '소화', '다양', '매력', '분위기', '아우라', '카리스마', '비주얼', '피지컬', '청순', '섹시', '쎈언니', '걸크러시',
    '찰떡', '어울리', '어울린다', '잘어울', '싱크로', '케미', '텐션', '센스', '유머', '작정', '본업', '장인', '프로',
    '퀄리티', '완성도', '고급', '세련', '감각', '감성', '힙', '트렌디', '신선', '참신', '기발', '독특', '개성',
    '중독', '계속', '반복', '또', '다시', '몇번째', '루프', '돌려봄', '킬링', '포인트', '임팩트',
    'good', 'great', 'best', 'love', 'amazing', 'awesome', 'beautiful', 'excellent', 'fantastic', 'perfect', 'happy',
    'incredible', 'brilliant', 'wow', 'omg', 'fire', 'goat', 'queen', 'king', 'icon', 'slay', 'legend', 'cute', 'pretty'}

NEGATIVE_WORDS = {'싫다', '싫어', '싫음', '별로', '별루', '최악', '실망', '실망했', '짜증', '짜증나', '짜증남',
    '화나', '화남', '답답', '불쾌', '슬프', '슬퍼', '우울', '우울해',
    '아쉽', '아쉬워', '걱정', '불안', '힘들', '피곤', '나쁘', '나빠', '못하', '못함', '후회', '혐오', '역겹', 
    '지루', '노잼', '재미없', '망했', '망함', '쓰레기', '불편', '비추', '극혐', '폭망', '실패',
    # 명확한 부정 표현만 유지 (모호한 표현 제거)
    'bad', 'worst', 'hate', 'terrible', 'awful', 'sad', 'angry', 'disappointed', 'boring', 'fail', 'trash', 'cringe', 'sucks'}

POSITIVE_EMOJIS = set('😀😃😄😁😆😅🤣😂😊😇🥰😍🤩😘👍👏🙌💪✨🌟⭐💖💗❤🧡💛💚💙💜💝🔥💯🎉👑💎🏆😎🤗🥳❤️')
NEGATIVE_EMOJIS = set('😢😭😤😠😡🤬💔👎🙄😒😞😔😟🙁😣😖😫😩😱🤮🤢')

# =============================================================================
# [NEW] 의견 유형 분류 키워드 사전 (v8.1 수정)
# =============================================================================
OPINION_TAXONOMY = {
    'product_service': {
        'name': '제품/서비스',
        'keywords': ['제품', '서비스', '앱', '어플', '프로그램', '소프트웨어', '기능', '업데이트', '버전', '출시',
                    '가격', '요금', '구독', '무료', '유료', '플랜', 'pro', 'premium', '결제', '환불', '품질',
                    'product', 'service', 'app', 'feature', 'update', 'price', 'subscription', '사용', '이용',
                    '증권', '은행', '카드', '보험', '통신', '배달', '쇼핑', '플랫폼'],
        'color': '#10b981'
    },
    'brand': {
        'name': '브랜드',
        'keywords': ['회사', '기업', '브랜드', '구글', 'google', '애플', 'apple', '삼성', 'samsung', '네이버', '카카오',
                    '현대', 'lg', 'sk', '롯데', '신세계', 'cj', '한화', '대기업', '스타트업', '광고주', '협찬사',
                    'nike', '나이키', 'adidas', '아디다스', '루이비통', '샤넬', '구찌', 'brand', 'company'],
        'color': '#f59e0b'
    },
    'market_social': {
        'name': '시장/사회적 영향',
        'keywords': ['일자리', '직업', '대체', '실업', '미래', '위험', '윤리', '규제', '법', '정책', '저작권',
                    '프라이버시', '개인정보', '보안', '사회', '영향', '변화', '트렌드', '세대', '문화', '논란',
                    'job', 'future', 'risk', 'regulation', 'ethics', 'trend', '경제', '시장', '업계'],
        'color': '#ef4444'
    },
    'model_person': {
        'name': '모델/출연자',
        'keywords': ['모델', '배우', '연예인', '아이돌', '가수', '출연', '캐스팅', '얼굴', '외모', '스타일', '패션',
                    '연기', '표정', '목소리', '매력', '분위기', '이미지', '비주얼', '피지컬', '아우라', '카리스마',
                    '팬', '덕질', '최애', '셀럽', 'celebrity', 'idol', 'actor', 'actress', '광고모델'],
        'color': '#ec4899'
    },
    'visual_aesthetic': {
        'name': '영상미/심미성',
        'keywords': ['영상미', '화질', '색감', '조명', '촬영', '구도', '편집', '연출', '감독', 'cg', '그래픽', '효과',
                    '아름답', '예쁘', '멋있', '화려', '고급', '세련', '감각', '퀄리티', '완성도', '디자인', '미적',
                    'beautiful', 'aesthetic', 'visual', 'quality', 'cinematic', '배경', '장면', '앵글', '무드'],
        'color': '#8b5cf6'
    },
    'fun_entertainment': {
        'name': '재미요소',
        'keywords': ['재밌', '재미', '웃기', '웃긴', '웃음', '유머', '센스', '킬링포인트', '중독', '계속', '반복',
                    '꿀잼', '핵잼', '존잼', '노잼', 'funny', 'fun', 'hilarious', 'lol', 'lmao', '개그', '코미디',
                    '병맛', '찰떡', '포인트', '임팩트', '신선', '참신', '기발', '아이디어', '컨셉', '스토리'],
        'color': '#06b6d4'
    }
}

# =============================================================================
# [NEW] 구매 여정 단계 키워드 사전
# =============================================================================
JOURNEY_STAGES = {
    'awareness': {
        'name': '인지 (Awareness)',
        'keywords': ['뭐야', '뭔지', '처음', '알게', '들어봤', '몰랐', '이런게', '신기', '오', '와', '헐',
                    'what is', 'first time', 'never knew', 'discover', '존재', '있었', '새로운'],
        'color': '#dbeafe'
    },
    'interest': {
        'name': '관심 (Interest)',
        'keywords': ['궁금', '알고싶', '더 알려', '어떻게', '방법', '가능', '될까', '할 수', '해볼',
                    'curious', 'how to', 'want to know', 'interesting', '관심', '찾아', '검색'],
        'color': '#dcfce7'
    },
    'consideration': {
        'name': '고려 (Consideration)',
        'keywords': ['비교', '차이', '뭐가 더', '어떤게', '추천', '고민', 'vs', '대', '장단점', '비용',
                    'compare', 'difference', 'which', 'recommend', 'pros cons', '선택', '결정'],
        'color': '#fef3c7'
    },
    'intent': {
        'name': '구매의도 (Intent)',
        'keywords': ['사야', '살까', '구매', '결제', '신청', '가입', '시작', '써볼', '해볼까', '질러',
                    'buy', 'purchase', 'subscribe', 'sign up', 'start', '돈', '투자', '지를까'],
        'color': '#fce7f3'
    },
    'experience': {
        'name': '경험 (Experience)',
        'keywords': ['써봤', '사용해봤', '해봤는데', '경험', '후기', '솔직히', '실제로', '직접', '결과',
                    'used', 'tried', 'experience', 'review', 'actually', '느낌', '체감', '만족', '불만'],
        'color': '#f3e8ff'
    }
}

# =============================================================================
# [NEW] 기대 요인 / 불안 요인 키워드
# =============================================================================
EXPECTATION_KEYWORDS = ['기대', '기대된다', '기다려', '얼른', '빨리', '곧', '언제', '출시', '업데이트', 
                        'excited', 'cant wait', 'looking forward', 'hope', '희망', '바람', '원해']
ANXIETY_KEYWORDS = ['걱정', '불안', '무섭', '두렵', '위험', '문제', '우려', '염려', '조심', '주의',
                   'worried', 'concern', 'scary', 'dangerous', 'risk', 'afraid', '대체', '사라질']

# =============================================================================
# 유틸리티 함수
# =============================================================================
def extract_video_id(url):
    if not url: return None
    patterns = [r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})', r'[?&]v=([a-zA-Z0-9_-]{11})']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return url if re.match(r'^[a-zA-Z0-9_-]{11}$', url) else None

def clean_text(text):
    if not isinstance(text, str): return ""
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def preprocess(text):
    text = clean_text(text).lower()
    text = re.compile("[" + u"\U0001F600-\U0001F64F" + u"\U0001F300-\U0001F5FF" + u"\U0001F680-\U0001F6FF" + u"\U0001F1E0-\U0001F1FF" + u"\U00002702-\U000027B0" + "]+", re.UNICODE).sub('', text)
    text = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', ' ', text)
    return ' '.join([t for t in text.split() if t not in STOPWORDS and len(t) > 1])

def format_date(d):
    return f"{d[:4]}년 {d[4:6]}월 {d[6:8]}일" if d and len(d) == 8 else "정보 없음"

def format_num(n):
    try:
        n = int(n) if n else 0
        if n >= 100000000: return f"{n/100000000:.1f}억"
        if n >= 10000: return f"{n/10000:.1f}만"
        if n >= 1000: return f"{n/1000:.1f}천"
        return f"{n:,}"
    except: return "0"

# =============================================================================
# [NEW] 언어 감지 함수
# =============================================================================
def detect_language(text: str) -> str:
    """댓글 텍스트의 언어를 감지"""
    if not text or len(text.strip()) < 3:
        return 'unknown'
    
    try:
        from langdetect import detect, LangDetectException
        try:
            lang = detect(text)
            # 주요 언어 매핑
            lang_map = {
                'ko': '한국어', 'en': '영어', 'ja': '일본어', 'zh-cn': '중국어', 'zh-tw': '중국어',
                'es': '스페인어', 'pt': '포르투갈어', 'fr': '프랑스어', 'de': '독일어',
                'ru': '러시아어', 'ar': '아랍어', 'hi': '힌디어', 'th': '태국어', 'vi': '베트남어',
                'id': '인도네시아어', 'ms': '말레이어', 'tl': '필리핀어'
            }
            return lang_map.get(lang, lang)
        except LangDetectException:
            return 'unknown'
    except ImportError:
        # langdetect 없으면 간단한 휴리스틱
        korean = len(re.findall(r'[가-힣]', text))
        english = len(re.findall(r'[a-zA-Z]', text))
        japanese = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        scores = {'한국어': korean, '영어': english, '일본어': japanese, '중국어': chinese}
        max_lang = max(scores, key=scores.get)
        return max_lang if scores[max_lang] > 0 else 'unknown'

def analyze_by_language(df: pd.DataFrame) -> Dict:
    """언어별 분석 수행"""
    if 'language' not in df.columns:
        return {}
    
    results = {}
    lang_counts = df['language'].value_counts()
    total = len(df)
    
    for lang in lang_counts.index:
        if lang == 'unknown':
            continue
        
        lang_df = df[df['language'] == lang]
        count = len(lang_df)
        
        if count < 5:  # 최소 5개 이상만 분석
            continue
        
        # 감성 분포
        sentiment_dist = lang_df['sentiment'].value_counts().to_dict()
        pos_pct = sentiment_dist.get('positive', 0) / count * 100
        neg_pct = sentiment_dist.get('negative', 0) / count * 100
        
        # 키워드
        texts = lang_df['text'].tolist()
        keywords = extract_keywords(texts, 5)
        
        results[lang] = {
            'count': count,
            'percentage': count / total * 100,
            'positive_pct': pos_pct,
            'negative_pct': neg_pct,
            'neutral_pct': 100 - pos_pct - neg_pct,
            'keywords': keywords,
            'sentiment_dist': sentiment_dist
        }
    
    return results

def generate_language_insight(lang_analysis: Dict) -> str:
    """언어별 분석 인사이트 생성"""
    if not lang_analysis:
        return ""
    
    insights = []
    sorted_langs = sorted(lang_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
    
    # 주요 언어 파악
    if sorted_langs:
        main_lang = sorted_langs[0][0]
        main_data = sorted_langs[0][1]
        insights.append(f"▸ **주요 시청층**: {main_lang} 사용자가 전체의 {main_data['percentage']:.0f}%를 차지합니다.")
        
        # 언어별 감성 차이
        if len(sorted_langs) > 1:
            sentiments = [(lang, data['positive_pct']) for lang, data in sorted_langs[:3]]
            most_positive = max(sentiments, key=lambda x: x[1])
            if most_positive[1] > main_data['positive_pct'] + 10:
                insights.append(f"▸ **언어별 온도차**: {most_positive[0]} 사용자가 가장 긍정적({most_positive[1]:.0f}%)으로, 해당 시장에서의 반응이 좋습니다.")
        
        # 글로벌 확장 가능성
        non_main_pct = 100 - main_data['percentage']
        if non_main_pct > 30:
            insights.append(f"▸ **글로벌 관심도**: 해외 시청자 비율이 {non_main_pct:.0f}%로, 다국어 콘텐츠 전략이 유효합니다.")
    
    return '\n\n'.join(insights)

# =============================================================================
# [NEW] 의견 유형 분류 함수
# =============================================================================
def classify_opinion_type(text: str) -> List[str]:
    """댓글을 의견 유형으로 분류 (복수 가능)"""
    if not text:
        return []
    
    text_lower = text.lower()
    categories = []
    
    for cat_id, cat_info in OPINION_TAXONOMY.items():
        for keyword in cat_info['keywords']:
            if keyword in text_lower:
                categories.append(cat_id)
                break
    
    return categories if categories else ['fun_entertainment']  # 기본값: 재미요소

def analyze_opinion_taxonomy(df: pd.DataFrame) -> Dict:
    """의견 유형별 분석"""
    if 'categories' not in df.columns:
        return {}
    
    results = {}
    total = len(df)
    
    for cat_id, cat_info in OPINION_TAXONOMY.items():
        # 해당 카테고리를 포함하는 댓글
        cat_df = df[df['categories'].apply(lambda x: cat_id in x)]
        count = len(cat_df)
        
        if count == 0:
            continue
        
        # 감성 분포
        sentiment_dist = cat_df['sentiment'].value_counts().to_dict()
        pos_pct = sentiment_dist.get('positive', 0) / count * 100
        neg_pct = sentiment_dist.get('negative', 0) / count * 100
        
        # 대표 댓글 (좋아요 상위)
        top_comment = cat_df.nlargest(1, 'like_count')
        sample = top_comment['text'].values[0][:100] if len(top_comment) > 0 else ""
        
        results[cat_id] = {
            'name': cat_info['name'],
            'count': count,
            'percentage': count / total * 100,
            'positive_pct': pos_pct,
            'negative_pct': neg_pct,
            'sample_comment': sample,
            'color': cat_info['color']
        }
    
    return results

def generate_taxonomy_insight(taxonomy_analysis: Dict) -> str:
    """의견 유형 분석 인사이트"""
    if not taxonomy_analysis:
        return ""
    
    insights = []
    sorted_cats = sorted(taxonomy_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
    
    if sorted_cats:
        top_cat = sorted_cats[0]
        insights.append(f"▸ **주요 관심사**: 시청자들은 '{top_cat[1]['name']}'에 가장 많은 의견을 남겼습니다 ({top_cat[1]['percentage']:.0f}%).")
        
        # 부정 비율 높은 카테고리
        negative_cats = [(cat_id, data) for cat_id, data in sorted_cats if data['negative_pct'] > 30]
        if negative_cats:
            neg_cat = max(negative_cats, key=lambda x: x[1]['negative_pct'])
            insights.append(f"▸ **주의 필요 영역**: '{neg_cat[1]['name']}' 관련 의견 중 {neg_cat[1]['negative_pct']:.0f}%가 부정적입니다. 해당 영역의 커뮤니케이션 점검이 필요합니다.")
        
        # 시장/사회적 영향 언급 시
        if 'market_social' in taxonomy_analysis and taxonomy_analysis['market_social']['percentage'] > 15:
            insights.append(f"▸ **사회적 관심**: 시청자들이 시장/사회적 영향에 대해 활발히 논의 중입니다. PR 메시지에 '책임감 있는 기술' 프레이밍을 고려하세요.")
    
    return '\n\n'.join(insights)

# =============================================================================
# [NEW] 구매 여정 분석 함수
# =============================================================================
def classify_journey_stage(text: str) -> str:
    """댓글을 구매 여정 단계로 분류"""
    if not text:
        return 'unknown'
    
    text_lower = text.lower()
    stage_scores = {}
    
    for stage_id, stage_info in JOURNEY_STAGES.items():
        score = sum(1 for kw in stage_info['keywords'] if kw in text_lower)
        stage_scores[stage_id] = score
    
    max_stage = max(stage_scores, key=stage_scores.get)
    return max_stage if stage_scores[max_stage] > 0 else 'unknown'

def analyze_journey_stages(df: pd.DataFrame) -> Dict:
    """구매 여정 단계별 분석"""
    if 'journey_stage' not in df.columns:
        return {}
    
    results = {}
    total = len(df)
    
    for stage_id, stage_info in JOURNEY_STAGES.items():
        stage_df = df[df['journey_stage'] == stage_id]
        count = len(stage_df)
        
        results[stage_id] = {
            'name': stage_info['name'],
            'count': count,
            'percentage': count / total * 100,
            'color': stage_info['color']
        }
    
    return results

def analyze_expectation_anxiety(df: pd.DataFrame) -> Dict:
    """기대 요인 vs 불안 요인 분석"""
    results = {'expectation': [], 'anxiety': []}
    
    for _, row in df.iterrows():
        text = str(row['text']).lower()
        
        # 기대 요인
        for kw in EXPECTATION_KEYWORDS:
            if kw in text:
                results['expectation'].append(row['text'][:100])
                break
        
        # 불안 요인
        for kw in ANXIETY_KEYWORDS:
            if kw in text:
                results['anxiety'].append(row['text'][:100])
                break
    
    return {
        'expectation_count': len(results['expectation']),
        'anxiety_count': len(results['anxiety']),
        'expectation_samples': results['expectation'][:3],
        'anxiety_samples': results['anxiety'][:3]
    }

# =============================================================================
# [NEW] 마케팅 전략 인사이트 생성 (고도화)
# =============================================================================
def generate_marketing_strategy_insight(
    df: pd.DataFrame, 
    keywords: List, 
    lang_analysis: Dict, 
    taxonomy_analysis: Dict,
    journey_analysis: Dict,
    expectation_anxiety: Dict,
    pos_pct: float,
    neg_pct: float
) -> str:
    """10년차 이상 마케터의 전략적 인사이트"""
    
    insights = []
    total = len(df)
    
    # 1. 구매 여정 기반 전략
    insights.append("### 📊 구매 여정 기반 전략")
    
    if journey_analysis:
        awareness = journey_analysis.get('awareness', {}).get('percentage', 0)
        intent = journey_analysis.get('intent', {}).get('percentage', 0)
        experience = journey_analysis.get('experience', {}).get('percentage', 0)
        
        if awareness > 30:
            insights.append(f"▸ **인지 단계 집중 ({awareness:.0f}%)**: 아직 제품/서비스를 처음 접하는 시청자가 많습니다. "
                          f"'이게 뭔지' 설명하는 콘텐츠가 효과적입니다. 복잡한 기능보다 **핵심 가치 1가지**를 반복 강조하세요.")
        
        if intent > 15:
            insights.append(f"▸ **구매 의도 신호 감지 ({intent:.0f}%)**: 실제 구매/가입을 고민하는 시청자가 있습니다. "
                          f"**CTA(Call-to-Action)를 명확히** 하고, 가격/혜택 정보를 영상 설명란에 정리하세요.")
        
        if experience > 20:
            insights.append(f"▸ **경험자 커뮤니티 ({experience:.0f}%)**: 이미 사용해본 시청자가 많습니다. "
                          f"이들을 **리뷰어/앰배서더**로 활용하면 신뢰도 높은 2차 콘텐츠가 생성됩니다.")
    
    # 2. 기대 vs 불안 밸런스
    insights.append("\n### ⚖️ 기대 vs 불안 요인 밸런스")
    
    exp_count = expectation_anxiety.get('expectation_count', 0)
    anx_count = expectation_anxiety.get('anxiety_count', 0)
    
    if exp_count > anx_count * 2:
        insights.append(f"▸ **긍정적 기대감 우세**: 기대 표현({exp_count}건)이 불안 표현({anx_count}건)의 2배 이상입니다. "
                       f"이 기대감을 **사전예약, 얼리버드 혜택**으로 전환하세요.")
    elif anx_count > exp_count:
        insights.append(f"▸ **불안 요인 해소 필요**: 불안/우려 표현({anx_count}건)이 기대({exp_count}건)보다 많습니다. "
                       f"FAQ 콘텐츠, 투명한 정보 공개로 **신뢰 회복**이 우선입니다.")
    
    # 불안 요인 샘플
    if expectation_anxiety.get('anxiety_samples'):
        insights.append(f"▸ **주요 불안 키워드**: {', '.join([s[:30] for s in expectation_anxiety['anxiety_samples'][:2]])}...")
    
    # 3. 언어별 메시지 전략
    if lang_analysis and len(lang_analysis) > 1:
        insights.append("\n### 🌍 언어별 메시지 전략")
        
        for lang, data in list(lang_analysis.items())[:3]:
            if data['positive_pct'] > 70:
                insights.append(f"▸ **{lang}**: 매우 우호적({data['positive_pct']:.0f}% 긍정). "
                               f"이 시장에서는 **팬 커뮤니티 구축**, 현지 인플루언서 협업이 효과적입니다.")
            elif data['negative_pct'] > 30:
                insights.append(f"▸ **{lang}**: 부정 비율 높음({data['negative_pct']:.0f}%). "
                               f"해당 시장의 **구체적 불만 요인**을 파악하고 현지화된 대응이 필요합니다.")
    
    # 4. 핵심 키워드 활용 전략
    if keywords:
        insights.append("\n### 🔑 키워드 활용 전략")
        top_kw = keywords[0][0] if keywords else ""
        insights.append(f"▸ **메인 키워드 '{top_kw}'**: 썸네일, 제목, 첫 3초에 이 키워드를 노출하면 CTR 상승이 예상됩니다.")
        
        if len(keywords) >= 3:
            secondary = [k for k, _ in keywords[1:4]]
            insights.append(f"▸ **서브 키워드**: {', '.join(secondary)} - SEO 태그와 설명란에 활용하세요.")
        
        # 해시태그 제안
        hashtags = [f"#{k.replace(' ', '')}" for k, _ in keywords[:5]]
        insights.append(f"▸ **추천 해시태그**: {' '.join(hashtags)}")
    
    # 5. 종합 전략 방향
    insights.append("\n### 🎯 종합 전략 방향")
    
    if pos_pct > 70:
        insights.append("▸ **공격적 확장 가능**: 긍정률이 매우 높아 바이럴 마케팅, 유료 광고 확대가 적합합니다. "
                       "지금이 **시장 점유율 확대**의 적기입니다.")
    elif pos_pct > 50:
        insights.append("▸ **점진적 성장 전략**: 긍정 기반이 있으나 열성 팬 전환이 필요합니다. "
                       "**정기 콘텐츠 + 커뮤니티 관리**에 집중하세요.")
    else:
        insights.append("▸ **신뢰 구축 우선**: 현재는 브랜드 인지도와 신뢰 구축이 먼저입니다. "
                       "**교육 콘텐츠, 투명한 커뮤니케이션**으로 기반을 다지세요.")
    
    return '\n\n'.join(insights)

# =============================================================================
# [NEW] 영상 정보 보완 체크
# =============================================================================
def generate_video_info_suggestions(video_info: Dict, total_comments: int, pos_pct: float) -> List[Dict]:
    """분석 신뢰도를 위한 추가 정보 제안"""
    suggestions = []
    
    view_count = video_info.get('view_count', 0)
    like_count = video_info.get('like_count', 0)
    
    # 1. 조회수 대비 댓글 비율
    if view_count > 0:
        comment_rate = total_comments / view_count * 100
        if comment_rate < 0.1:
            suggestions.append({
                'title': '댓글 참여율 낮음',
                'desc': f'조회수 대비 댓글 비율이 {comment_rate:.3f}%로 낮습니다. 시청자 참여를 유도하는 CTA가 필요할 수 있습니다.',
                'type': 'warning'
            })
        elif comment_rate > 1:
            suggestions.append({
                'title': '높은 참여도',
                'desc': f'댓글 참여율 {comment_rate:.2f}%로 매우 활발합니다. 논쟁적 주제이거나 충성 팬층이 있습니다.',
                'type': 'info'
            })
    
    # 2. 좋아요/조회수 비율
    if view_count > 0 and like_count > 0:
        like_rate = like_count / view_count * 100
        if like_rate < 2:
            suggestions.append({
                'title': '좋아요 전환율 점검',
                'desc': f'좋아요 비율 {like_rate:.1f}%는 평균 이하입니다. 콘텐츠 만족도 또는 CTA 위치를 점검하세요.',
                'type': 'warning'
            })
    
    # 3. 광고 여부 추정
    suggestions.append({
        'title': '광고/협찬 여부 확인 권장',
        'desc': '댓글에서 광고 관련 반응이 있는지 확인하세요. 협찬 콘텐츠는 감성 분석 해석에 영향을 줄 수 있습니다.',
        'type': 'info'
    })
    
    # 4. 업로드 시점 대비 반응
    suggestions.append({
        'title': '시간 경과에 따른 반응 변화',
        'desc': '업로드 직후 vs 현재 반응 비교 분석이 필요합니다. 초기 반응과 장기 반응은 다를 수 있습니다.',
        'type': 'info'
    })
    
    # 5. 부정률 높을 때
    if pos_pct < 50:
        suggestions.append({
            'title': '부정 댓글 원인 심층 분석',
            'desc': '긍정률이 50% 미만입니다. 부정 댓글의 구체적인 불만 사항을 별도로 분류 분석하는 것을 권장합니다.',
            'type': 'warning'
        })
    
    return suggestions

# =============================================================================
# 댓글 수집
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def collect_comments(url, max_comments):
    """
    댓글 수집 기준: YouTube API의 'top' (인기순) 정렬
    - 좋아요 수가 많은 댓글이 우선 수집됨
    - 최대 max_comments개까지만 수집
    """
    import yt_dlp
    opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'getcomments': True,
            'extractor_args': {'youtube': {'max_comments': [str(max_comments)], 'comment_sort': ['top']}}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info: return None, []
        
        total_comment_count = info.get('comment_count', 0) or 0
        
        video_info = {
            'title': info.get('title', '제목 없음'),
            'channel': info.get('channel', info.get('uploader', '')),
            'thumbnail': info.get('thumbnail', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'comment_count': total_comment_count,  # 전체 댓글 수
            'upload_date': format_date(info.get('upload_date', '')),
            'upload_date_raw': info.get('upload_date', ''),
            'url': url,
        }
        raw = info.get('comments') or []
        comments = [{'text': c.get('text', ''), 'like_count': c.get('like_count', 0) or 0} for c in raw[:max_comments] if c]
        return video_info, comments

# =============================================================================
# 감성 분석 (v8.1 개선: 긍부정 분류 정확도 향상)
# =============================================================================
def analyze_sentiment(text):
    """
    감성 분석 기준:
    - 긍정/부정 이모지 비율
    - 긍정/부정 키워드 매칭
    - 웃음 표현 (ㅋㅋ, ㅎㅎ) → 긍정 가중치
    - 감탄/강조 표현 (!, 하, 와, 오) → 맥락에 따라 판단
    """
    if not text: return 'neutral', 0.0
    text_lower = text.lower()
    score = 0.0
    
    # 1. 이모지 분석
    pos_e = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_e = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    if pos_e + neg_e > 0: 
        score += (pos_e - neg_e) / (pos_e + neg_e + 1) * 1.5
    
    # 2. 키워드 분석
    words = set(re.findall(r'[가-힣]+|[a-z]+', text_lower))
    pos_w = sum(1 for w in words if any(pw in w or w in pw for pw in POSITIVE_WORDS))
    neg_w = sum(1 for w in words if any(nw in w or w in nw for nw in NEGATIVE_WORDS))
    if pos_w + neg_w > 0: 
        score += (pos_w - neg_w) / (pos_w + neg_w + 0.5)
    
    # 3. 웃음 표현 (ㅋㅋ, ㅎㅎ) → 강한 긍정 신호
    laugh_pattern = re.findall(r'ㅋ{2,}|ㅎ{2,}|ㄱㅋ+', text)
    if laugh_pattern:
        laugh_count = len(laugh_pattern)
        score += 0.4 * min(laugh_count, 3)  # 최대 1.2까지 가중치
    
    # 4. 감탄 표현 분석 (맥락 고려)
    # "하 진짜" 같은 표현은 웃음 표현과 함께 있으면 긍정
    exclaim_pattern = re.search(r'^(하|와|오|우와|헐|대박)\s', text)
    if exclaim_pattern:
        if laugh_pattern or pos_w > 0:  # 웃음이나 긍정 키워드와 함께면 긍정
            score += 0.3
        # 부정 키워드 없이 단독이면 중립 유지 (score 변경 없음)
    
    # 5. 느낌표 (긍정 맥락에서만 가중치)
    exclamation_count = text.count('!')
    if exclamation_count >= 2 and neg_w == 0:
        score += 0.2
    
    # 6. 부정 패턴 (명확한 경우만)
    if re.search(r'ㅡㅡ+|;;+|\.\.\.+$', text) and pos_w == 0:
        score -= 0.3
    
    # 7. 최종 판정 (임계값 조정)
    if score > 0.15:  # 긍정 임계값 약간 상향
        return 'positive', min(score, 1.0)
    elif score < -0.2:  # 부정 임계값 상향 (더 명확해야 부정)
        return 'negative', max(score, -1.0)
    return 'neutral', score

# =============================================================================
# 키워드 추출
# =============================================================================
def extract_keywords(texts, top_n=15):
    words = []
    for t in texts:
        if t: words.extend(preprocess(str(t)).split())
    return Counter(words).most_common(top_n) if words else []

# =============================================================================
# 차트
# =============================================================================
def create_donut_chart(pos, neu, neg):
    colors = ['#1e3a5f', '#5a7fa8', '#a8c5de']
    fig = go.Figure(data=[go.Pie(
        values=[pos, neu, neg], labels=['긍정', '중립', '부정'], hole=0.55,
        marker=dict(colors=colors), textinfo='percent', textfont=dict(size=13, color='white'),
        hovertemplate='%{label}: %{value}개<br>%{percent}<extra></extra>', sort=False
    )])
    fig.update_layout(
        showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5, font=dict(size=11)),
        margin=dict(t=20, b=40, l=20, r=20), height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    total = pos + neu + neg
    fig.add_annotation(text=f"<b>{total:,}</b><br><span style='font-size:10px;color:#64748b'>댓글</span>",
                      x=0.5, y=0.5, font=dict(size=16, color='#1e3a5f'), showarrow=False)
    return fig

def create_keyword_chart(keywords):
    if not keywords: return None
    kw_list = keywords[:10]
    labels = [k for k, _ in kw_list][::-1]
    values = [v for _, v in kw_list][::-1]
    n = len(labels)
    colors = [f'rgba(30, 58, 95, {0.3 + 0.7 * i / (n-1 if n > 1 else 1)})' for i in range(n)]
    
    fig = go.Figure(data=[go.Bar(
        x=values, y=labels, orientation='h', marker=dict(color=colors),
        text=values, textposition='outside', textfont=dict(size=10, color='#1e3a5f'),
        hovertemplate='%{y}: %{x}회<extra></extra>'
    )])
    fig.update_layout(
        margin=dict(t=20, b=20, l=10, r=40), height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color='#334155')), bargap=0.3,
    )
    return fig

def create_taxonomy_chart(taxonomy_analysis: Dict):
    """의견 유형 분포 차트"""
    if not taxonomy_analysis:
        return None
    
    labels = [data['name'] for data in taxonomy_analysis.values()]
    values = [data['percentage'] for data in taxonomy_analysis.values()]
    colors = [data['color'] for data in taxonomy_analysis.values()]
    
    fig = go.Figure(data=[go.Bar(
        x=values, y=labels, orientation='h',
        marker=dict(color=colors),
        text=[f'{v:.0f}%' for v in values],
        textposition='outside',
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
    )])
    fig.update_layout(
        margin=dict(t=20, b=20, l=10, r=50), height=220,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, max(values)*1.3]),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        bargap=0.4,
    )
    return fig

def create_journey_chart(journey_analysis: Dict):
    """구매 여정 퍼널 차트"""
    if not journey_analysis:
        return None
    
    stages = ['awareness', 'interest', 'consideration', 'intent', 'experience']
    labels = [journey_analysis.get(s, {}).get('name', s) for s in stages]
    values = [journey_analysis.get(s, {}).get('percentage', 0) for s in stages]
    colors = [JOURNEY_STAGES[s]['color'] for s in stages]
    
    fig = go.Figure(data=[go.Funnel(
        y=labels, x=values,
        textinfo="value+percent total",
        marker=dict(color=['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']),
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
    )])
    fig.update_layout(
        margin=dict(t=20, b=20, l=10, r=10), height=280,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

# =============================================================================
# PDF 생성 (고도화)
# =============================================================================
def generate_pdf_report(
    video_info, total, pos, neu, neg, pos_pct, neg_pct,
    keywords, top_pos_comments, top_neg_comments,
    lang_analysis, taxonomy_analysis, journey_analysis,
    expectation_anxiety, marketing_insight, video_suggestions
):
    """고급 분석이 포함된 PDF 리포트"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import urllib.request
    import os
    
    # 한글 폰트
    font_path = '/tmp/NotoSansKR-Regular.ttf'
    font_bold_path = '/tmp/NotoSansKR-Bold.ttf'
    
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve('https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Regular.ttf', font_path)
            urllib.request.urlretrieve('https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Bold.ttf', font_bold_path)
        except: pass
    
    try:
        pdfmetrics.registerFont(TTFont('NotoSansKR', font_path))
        pdfmetrics.registerFont(TTFont('NotoSansKR-Bold', font_bold_path))
        font_name, font_bold = 'NotoSansKR', 'NotoSansKR-Bold'
    except:
        font_name, font_bold = 'Helvetica', 'Helvetica-Bold'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='KTitle', fontName=font_bold, fontSize=16, textColor=colors.HexColor('#1e3a5f'), spaceAfter=8))
    styles.add(ParagraphStyle(name='KHeading', fontName=font_bold, fontSize=11, textColor=colors.HexColor('#1e3a5f'), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='KBody', fontName=font_name, fontSize=9, textColor=colors.HexColor('#334155'), leading=14))
    styles.add(ParagraphStyle(name='KSmall', fontName=font_name, fontSize=8, textColor=colors.HexColor('#64748b'), leading=12))
    
    story = []
    
    # 제목
    story.append(Paragraph("유튜브 댓글 인사이트 리포트 v8.1", styles['KTitle']))
    story.append(Paragraph(f"생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['KSmall']))
    story.append(Spacer(1, 8))
    
    # 영상 정보
    story.append(Paragraph("📺 영상 정보", styles['KHeading']))
    info_data = [
        ['제목', video_info.get('title', '')[:45] + ('...' if len(video_info.get('title', '')) > 45 else '')],
        ['채널', video_info.get('channel', '')],
        ['업로드', video_info.get('upload_date', '')],
        ['조회수', format_num(video_info.get('view_count', 0))],
        ['좋아요', format_num(video_info.get('like_count', 0))],
    ]
    t = Table(info_data, colWidths=[50, 420])
    t.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('FONTSIZE', (0,0), (-1,-1), 9),
                           ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#64748b')), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 8))
    
    # 핵심 지표
    story.append(Paragraph("📊 감성 분석", styles['KHeading']))
    sent_data = [['분석 댓글', f'{total:,}개', '긍정률', f'{pos_pct:.1f}%', '부정률', f'{neg_pct:.1f}%']]
    t = Table(sent_data, colWidths=[55, 60, 45, 50, 45, 50])
    t.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('FONTSIZE', (0,0), (-1,-1), 9),
                           ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(t)
    story.append(Spacer(1, 8))
    
    # 키워드
    story.append(Paragraph("🔑 핵심 키워드", styles['KHeading']))
    if keywords:
        kw_text = ', '.join([f"{k}({v})" for k, v in keywords[:10]])
        story.append(Paragraph(kw_text, styles['KBody']))
    story.append(Spacer(1, 8))
    
    # 언어별 분석
    if lang_analysis:
        story.append(Paragraph("🌍 언어별 반응", styles['KHeading']))
        for lang, data in list(lang_analysis.items())[:4]:
            story.append(Paragraph(f"• {lang}: {data['count']}건 ({data['percentage']:.0f}%) | 긍정 {data['positive_pct']:.0f}%", styles['KBody']))
        story.append(Spacer(1, 8))
    
    # 의견 유형
    if taxonomy_analysis:
        story.append(Paragraph("🧩 의견 유형별 분포", styles['KHeading']))
        for cat_id, data in taxonomy_analysis.items():
            story.append(Paragraph(f"• {data['name']}: {data['percentage']:.0f}% (긍정 {data['positive_pct']:.0f}%)", styles['KBody']))
        story.append(Spacer(1, 8))
    
    # 구매 여정
    if journey_analysis:
        story.append(Paragraph("🛒 구매 여정 분포", styles['KHeading']))
        for stage_id in ['awareness', 'interest', 'consideration', 'intent', 'experience']:
            data = journey_analysis.get(stage_id, {})
            if data.get('percentage', 0) > 0:
                story.append(Paragraph(f"• {data.get('name', stage_id)}: {data.get('percentage', 0):.0f}%", styles['KBody']))
        story.append(Spacer(1, 8))
    
    # 기대 vs 불안
    story.append(Paragraph("⚖️ 기대 vs 불안 요인", styles['KHeading']))
    story.append(Paragraph(f"• 기대 표현: {expectation_anxiety.get('expectation_count', 0)}건", styles['KBody']))
    story.append(Paragraph(f"• 불안 표현: {expectation_anxiety.get('anxiety_count', 0)}건", styles['KBody']))
    story.append(Spacer(1, 8))
    
    # 마케팅 전략 인사이트
    story.append(PageBreak())
    story.append(Paragraph("🎯 마케팅 전략 인사이트", styles['KHeading']))
    if marketing_insight:
        clean_insight = marketing_insight.replace('**', '').replace('###', '■').replace('▸', '•')
        for para in clean_insight.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip()[:300], styles['KBody']))
                story.append(Spacer(1, 3))
    story.append(Spacer(1, 8))
    
    # 추가 필요 정보
    story.append(Paragraph("📌 분석 보완 제안", styles['KHeading']))
    for sug in video_suggestions[:3]:
        story.append(Paragraph(f"• {sug['title']}: {sug['desc'][:80]}...", styles['KSmall']))
    story.append(Spacer(1, 8))
    
    # 주요 댓글
    story.append(Paragraph("💬 주요 긍정 댓글", styles['KHeading']))
    for c in top_pos_comments[:2]:
        story.append(Paragraph(f'"{c["text"][:80]}..." (👍{c["like_count"]:,})', styles['KSmall']))
    
    story.append(Paragraph("💬 주요 부정 댓글", styles['KHeading']))
    for c in top_neg_comments[:2]:
        story.append(Paragraph(f'"{c["text"][:80]}..." (👍{c["like_count"]:,})', styles['KSmall']))
    
    # 푸터
    story.append(Spacer(1, 15))
    story.append(Paragraph("─" * 60, styles['KSmall']))
    story.append(Paragraph("유튜브 댓글 인사이트 분석기 v8.1 | 자동 생성 리포트", styles['KSmall']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 헤더
    st.markdown('''
    <div class="header">
        <h1>📊 유튜브 댓글 인사이트 분석기</h1>
        <p>AI 기반 고급 댓글 분석 · 마케팅 전략 인사이트</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 입력
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        url = st.text_input("URL", placeholder="https://www.youtube.com/watch?v=...", 
                           label_visibility="collapsed", key=f"url_input_{st.session_state.input_key}")
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            btn = st.button("🔍 분석 시작", use_container_width=True)
        with col_btn2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state.input_key += 1
                st.rerun()
    
    if btn and url:
        vid = extract_video_id(url)
        if not vid:
            st.error("❌ 유효하지 않은 URL입니다.")
            return
        
        try:
            # =====================================================================
            # 데이터 수집 및 분석
            # =====================================================================
            progress = st.progress(0, "댓글 수집 중...")
            video_info, comments = collect_comments(url, CONFIG["max_comments"])
            
            if not video_info or not comments:
                st.warning("⚠️ 댓글을 가져올 수 없습니다.")
                return
            
            progress.progress(20, "감성 분석 중...")
            df = pd.DataFrame(comments)
            results = [analyze_sentiment(str(t)) for t in df['text'].fillna('')]
            df['sentiment'] = [r[0] for r in results]
            
            progress.progress(40, "언어 감지 중...")
            df['language'] = df['text'].apply(detect_language)
            
            progress.progress(50, "의견 유형 분류 중...")
            df['categories'] = df['text'].apply(classify_opinion_type)
            
            progress.progress(60, "구매 여정 분석 중...")
            df['journey_stage'] = df['text'].apply(classify_journey_stage)
            
            progress.progress(70, "키워드 분석 중...")
            keywords = extract_keywords(df['text'].tolist(), CONFIG["top_keywords_count"])
            
            progress.progress(80, "고급 분석 중...")
            lang_analysis = analyze_by_language(df)
            taxonomy_analysis = analyze_opinion_taxonomy(df)
            journey_analysis = analyze_journey_stages(df)
            expectation_anxiety = analyze_expectation_anxiety(df)
            
            progress.progress(90, "인사이트 생성 중...")
            
            # 기본 통계
            total = len(df)
            pos = int((df['sentiment'] == 'positive').sum())
            neu = int((df['sentiment'] == 'neutral').sum())
            neg = int((df['sentiment'] == 'negative').sum())
            pos_pct = pos / total * 100 if total else 0
            neg_pct = neg / total * 100 if total else 0
            
            # 마케팅 인사이트 생성
            marketing_insight = generate_marketing_strategy_insight(
                df, keywords, lang_analysis, taxonomy_analysis, 
                journey_analysis, expectation_anxiety, pos_pct, neg_pct
            )
            
            # 영상 정보 보완 제안
            video_suggestions = generate_video_info_suggestions(video_info, total, pos_pct)
            
            # 주요 댓글
            top_pos_df = df[df['sentiment'] == 'positive'].nlargest(3, 'like_count')
            top_neg_df = df[df['sentiment'] == 'negative'].nlargest(3, 'like_count')
            top_pos_comments = top_pos_df.to_dict('records')
            top_neg_comments = top_neg_df.to_dict('records')
            
            progress.progress(100, "완료!")
            progress.empty()
            
            # =====================================================================
            # UI 렌더링
            # =====================================================================
            
            # 영상 정보 박스
            st.markdown('<div class="video-info-box">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2.5])
            with c1:
                if video_info.get('thumbnail'):
                    st.image(video_info['thumbnail'], use_container_width=True)
            with c2:
                st.markdown(f"### {video_info.get('title', '')}")
                st.markdown(f'''
                <div class="video-info-row"><span class="video-info-label">채널명</span><span class="video-info-value">{video_info.get('channel', '')}</span></div>
                <div class="video-info-row"><span class="video-info-label">업로드 날짜</span><span class="video-info-value">{video_info.get('upload_date', '')}</span></div>
                <div class="video-info-row"><span class="video-info-label">조회수</span><span class="video-info-value">{format_num(video_info.get('view_count', 0))}</span></div>
                <div class="video-info-row"><span class="video-info-label">좋아요</span><span class="video-info-value">{format_num(video_info.get('like_count', 0))}</span></div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 핵심 지표
            total_comments = video_info.get('comment_count', 0)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            if total_comments > CONFIG["max_comments"]:
                c1.metric("분석 댓글", f"{total:,}개", delta=f"전체 {format_num(total_comments)}개 중")
            else:
                c1.metric("분석 댓글", f"{total:,}개")
            c2.metric("긍정률", f"{pos_pct:.1f}%")
            c3.metric("부정률", f"{neg_pct:.1f}%")
            c4.metric("언어 수", f"{len(lang_analysis)}개")
            c5.metric("의견 유형", f"{len(taxonomy_analysis)}개")
            
            # 1000개 초과 시 안내 문구
            if total_comments > CONFIG["max_comments"]:
                st.info(f"ℹ️ 전체 댓글 {format_num(total_comments)}개 중 **좋아요(인기) 순으로 상위 {CONFIG['max_comments']:,}개**만 분석했습니다. 인기 댓글 위주의 분석 결과입니다.")
            
            # PDF 다운로드
            try:
                pdf_buffer = generate_pdf_report(
                    video_info, total, pos, neu, neg, pos_pct, neg_pct,
                    keywords, top_pos_comments, top_neg_comments,
                    lang_analysis, taxonomy_analysis, journey_analysis,
                    expectation_anxiety, marketing_insight, video_suggestions
                )
                st.download_button("📄 PDF 리포트 다운로드", data=pdf_buffer,
                                  file_name=f"youtube_insight_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                  mime="application/pdf")
            except Exception as e:
                st.caption(f"PDF 생성 불가: {e}")
            
            # =====================================================================
            # 📊 기본 분석
            # =====================================================================
            st.markdown('<div class="section-title">📊 감성 분석 결과</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**감성 분포**")
                st.plotly_chart(create_donut_chart(pos, neu, neg), use_container_width=True, config={'displayModeBar': False})
                st.caption("📌 분석 기준: 긍정/부정 키워드, 이모지, 웃음 표현(ㅋㅋ, ㅎㅎ) 등을 종합 분석")
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**핵심 키워드**")
                if keywords:
                    st.plotly_chart(create_keyword_chart(keywords), use_container_width=True, config={'displayModeBar': False})
                st.caption("📌 숫자 = 해당 키워드가 댓글에서 언급된 횟수")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # =====================================================================
            # 💬 주요 댓글 (감성 분석 바로 다음으로 이동)
            # =====================================================================
            st.markdown('<div class="section-title">💬 주요 댓글</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("**👍 긍정 TOP 3**")
                for c in top_pos_comments:
                    txt = str(c['text'])[:100] + ('...' if len(str(c['text'])) > 100 else '')
                    st.markdown(f'''<div class="comment pos">
                        <div class="comment-text">"{txt}"</div>
                        <div class="comment-likes">👍 {int(c['like_count']):,}</div>
                    </div>''', unsafe_allow_html=True)
            
            with c2:
                st.markdown("**👎 부정 TOP 3**")
                if top_neg_comments:
                    for c in top_neg_comments:
                        txt = str(c['text'])[:100] + ('...' if len(str(c['text'])) > 100 else '')
                        st.markdown(f'''<div class="comment neg">
                            <div class="comment-text">"{txt}"</div>
                            <div class="comment-likes">👍 {int(c['like_count']):,}</div>
                        </div>''', unsafe_allow_html=True)
                else:
                    st.success("🎉 부정 댓글이 거의 없습니다!")
            
            # =====================================================================
            # 🌍 언어별 분석
            # =====================================================================
            if lang_analysis:
                st.markdown('<div class="section-title">🌍 언어별 분석</div>', unsafe_allow_html=True)
                
                # 언어 태그
                lang_tags = ' '.join([f'<span class="lang-tag{"" if i > 0 else " primary"}">{lang} ({data["percentage"]:.0f}%)</span>' 
                                     for i, (lang, data) in enumerate(sorted(lang_analysis.items(), key=lambda x: -x[1]['count']))])
                st.markdown(f'<div style="margin-bottom:1rem">{lang_tags}</div>', unsafe_allow_html=True)
                
                # 언어별 상세
                cols = st.columns(min(len(lang_analysis), 3))
                for i, (lang, data) in enumerate(list(lang_analysis.items())[:3]):
                    with cols[i]:
                        st.markdown(f'''<div class="card">
                            <div style="font-weight:600;color:#1e3a5f;margin-bottom:0.5rem">{lang}</div>
                            <div style="font-size:0.85rem;color:#475569">
                                댓글 {data['count']:,}개 ({data['percentage']:.0f}%)<br>
                                긍정 {data['positive_pct']:.0f}% · 부정 {data['negative_pct']:.0f}%<br>
                                키워드: {', '.join([k for k, _ in data['keywords'][:3]])}
                            </div>
                        </div>''', unsafe_allow_html=True)
                
                # 인사이트
                lang_insight = generate_language_insight(lang_analysis)
                if lang_insight:
                    st.markdown(f'<div class="insight"><div class="insight-desc">{lang_insight}</div></div>', unsafe_allow_html=True)
            
            # =====================================================================
            # 🧩 의견 유형별 분석
            # =====================================================================
            if taxonomy_analysis:
                st.markdown('<div class="section-title">🧩 댓글 유형별 분석</div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns([1.2, 1])
                with c1:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("**의견 유형 분포**")
                    fig = create_taxonomy_chart(taxonomy_analysis)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with c2:
                    st.markdown("**유형별 대표 의견**")
                    for cat_id, data in list(taxonomy_analysis.items())[:3]:
                        if data['sample_comment']:
                            st.markdown(f'''<div class="category-card" style="border-color:{data['color']}">
                                <div class="category-title">{data['name']}</div>
                                <div class="category-pct">{data['percentage']:.0f}% · 긍정 {data['positive_pct']:.0f}%</div>
                                <div class="category-sample">"{data['sample_comment'][:60]}..."</div>
                            </div>''', unsafe_allow_html=True)
                
                # 인사이트
                taxonomy_insight = generate_taxonomy_insight(taxonomy_analysis)
                if taxonomy_insight:
                    st.markdown(f'<div class="insight"><div class="insight-desc">{taxonomy_insight}</div></div>', unsafe_allow_html=True)
            
            # =====================================================================
            # 🎯 마케팅 전략 인사이트
            # =====================================================================
            st.markdown('<div class="section-title">🎯 마케팅 전략 인사이트</div>', unsafe_allow_html=True)
            
            # 구매 여정 퍼널
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**구매 여정 분포**")
                journey_fig = create_journey_chart(journey_analysis)
                if journey_fig:
                    st.plotly_chart(journey_fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**기대 vs 불안 요인**")
                exp_c = expectation_anxiety.get('expectation_count', 0)
                anx_c = expectation_anxiety.get('anxiety_count', 0)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f'''<div class="stat-box">
                        <div class="stat-value">{exp_c}</div>
                        <div class="stat-label">기대 표현</div>
                    </div>''', unsafe_allow_html=True)
                with col_b:
                    st.markdown(f'''<div class="stat-box-light">
                        <div class="stat-value">{anx_c}</div>
                        <div class="stat-label">불안 표현</div>
                    </div>''', unsafe_allow_html=True)
                
                if expectation_anxiety.get('anxiety_samples'):
                    st.markdown("**주요 불안 키워드:**")
                    for sample in expectation_anxiety['anxiety_samples'][:2]:
                        st.caption(f'"{sample[:50]}..."')
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 마케팅 인사이트 상세
            if marketing_insight:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(marketing_insight)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # =====================================================================
            # 📌 추가 필요 정보
            # =====================================================================
            st.markdown('<div class="section-title">📌 분석 보완을 위한 추가 정보</div>', unsafe_allow_html=True)
            
            for sug in video_suggestions:
                box_class = "warning-box" if sug['type'] == 'warning' else "info-box"
                st.markdown(f'''<div class="{box_class}">
                    <strong>{sug['title']}</strong><br>
                    <span style="font-size:0.9rem">{sug['desc']}</span>
                </div>''', unsafe_allow_html=True)
            
            st.markdown('<div class="footer">유튜브 댓글 인사이트 분석기 v8.1</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
