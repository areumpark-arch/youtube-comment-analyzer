#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 분석기 v2.0
========================
- 맥락 기반 감성 분석 개선
- 키워드/핵심 요인 분석 추가
- Claude 스타일 디자인
"""

import streamlit as st
import pandas as pd
import re
from collections import Counter

# =============================================================================
# 설정
# =============================================================================
MAX_COMMENTS = 500

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# Claude 스타일 CSS
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #FAF9F7;
    }
    
    .block-container {
        max-width: 900px !important;
        padding: 2rem 1.5rem !important;
    }
    
    /* 헤더 */
    .header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .header h1 {
        font-size: 1.6rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.3rem;
    }
    .header p {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* 카드 */
    .card {
        background: #FFFFFF;
        border: 1px solid #E8E5E0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* 섹션 제목 */
    .section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #8B7355;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.8rem;
    }
    
    /* 영상 정보 */
    .video-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }
    .video-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        color: #666;
        font-size: 0.85rem;
    }
    .video-meta-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    
    /* 감성 바 */
    .sentiment-bar {
        display: flex;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin: 1rem 0;
    }
    .sentiment-pos { background: #D4A574; }
    .sentiment-neu { background: #E8E5E0; }
    .sentiment-neg { background: #A0A0A0; }
    
    .sentiment-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #666;
    }
    .sentiment-label {
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    .dot-pos { background: #D4A574; }
    .dot-neu { background: #E8E5E0; border: 1px solid #ccc; }
    .dot-neg { background: #A0A0A0; }
    
    /* 키워드 */
    .keyword-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .keyword-tag {
        background: #F5F3F0;
        border: 1px solid #E8E5E0;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        color: #5a5a5a;
    }
    .keyword-tag strong {
        color: #1a1a1a;
    }
    
    /* 요인 분석 */
    .factor-box {
        background: #F5F3F0;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .factor-title {
        font-weight: 600;
        color: #1a1a1a;
        font-size: 0.9rem;
        margin-bottom: 0.4rem;
    }
    .factor-desc {
        color: #666;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    
    /* 댓글 */
    .comment-section-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.6rem;
    }
    .comment-item {
        background: #F9F8F6;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.5rem;
    }
    .comment-item.best {
        background: #FDF8F3;
        border-left: 3px solid #D4A574;
    }
    .comment-item.positive {
        border-left: 3px solid #D4A574;
    }
    .comment-item.negative {
        border-left: 3px solid #A0A0A0;
    }
    .comment-text {
        color: #333;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 0.3rem;
    }
    .comment-meta {
        color: #999;
        font-size: 0.75rem;
    }
    
    /* 인사이트 */
    .insight-box {
        background: #1a1a1a;
        color: #fff;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    }
    .insight-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #D4A574;
        margin-bottom: 0.5rem;
    }
    .insight-text {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #eee;
    }
    
    /* 경고/안내 */
    .notice {
        background: #FDF8F3;
        border: 1px solid #E8DFD5;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.8rem;
        color: #8B7355;
        margin: 0.5rem 0;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #999;
        font-size: 0.75rem;
    }
    
    /* Streamlit 기본 요소 */
    #MainMenu, footer, .stDeployButton {display: none;}
    
    .stTextInput > div > div > input {
        background: #FFFFFF;
        border: 1px solid #E8E5E0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #D4A574;
        box-shadow: 0 0 0 2px rgba(212, 165, 116, 0.1);
    }
    
    .stButton > button {
        background: #1a1a1a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-size: 0.9rem;
        font-weight: 500;
        width: 100%;
    }
    .stButton > button:hover {
        background: #333;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 감성 분석 (맥락 기반 개선)
# =============================================================================

# 긍정 표현
POSITIVE_EXPRESSIONS = {
    '좋아', '좋다', '좋네', '좋은', '좋았', '좋음',
    '최고', '대박', '멋지', '멋져', '멋있', '예쁘', '예뻐', '이쁘', '이뻐',
    '귀엽', '귀여', '사랑', '감사', '고마', '행복', '기쁘', '즐거',
    '훌륭', '완벽', '감동', '재밌', '재미있', '웃기', '웃겨', '힐링',
    '짱', '쩔어', '쩐다', '미쳤', '대단', '놀랍', '신기',
    '레전드', '갓', '인정', '추천', '천재', '역시', '찐',
    '꿀잼', '핵잼', '존잼', '킬링', '중독', '센스',
    '소화', '매력', '찰떡', '어울려', '어울리', '퀄리티',
    'good', 'great', 'best', 'love', 'amazing', 'awesome', 'perfect', 'wow',
}

# 부정 표현
NEGATIVE_EXPRESSIONS = {
    '싫어', '싫다', '별로', '최악', '실망', '짜증', '화나', '열받',
    '답답', '불쾌', '불편', '슬프', '슬퍼', '우울',
    '지루', '노잼', '재미없', '못생', '쓰레기', '망했', '폭망',
    '극혐', '혐오', '역겹', '비추', '후회', '아깝',
    'bad', 'worst', 'hate', 'terrible', 'boring', 'trash', 'cringe',
}

# 부정 전환 패턴 (긍정어 + 이 패턴 = 부정)
NEGATION_PATTERNS = [
    r'재미\s*없', r'재밌지\s*않', r'좋지\s*않', r'좋은\s*거\s*없',
    r'별로', r'아닌', r'아니', r'없어', r'없다', r'없네', r'없음',
    r'못\s*하', r'안\s*좋', r'글쎄', r'싫',
]

# 아이러니/반어 패턴 (웃음 + 부정 맥락)
IRONY_NEGATIVE_PATTERNS = [
    r'어이없', r'황당', r'기가\s*막', r'할말없', r'말문이', r'헛웃음',
    r'웃프', r'웃기지도\s*않', r'피식', r'실소', r'냉소',
    r'뭐지', r'뭐야', r'왜이래', r'왜이러',
]

# 긍정적 욕설 패턴 (욕설이지만 긍정 맥락)
POSITIVE_SWEAR_CONTEXT = [
    r'미친\s*(연기|실력|퀄|비주얼|텐션|센스)',
    r'개\s*(잘|멋|예쁘|귀엽|웃기)',
    r'ㅅㅂ.{0,10}(좋|최고|대박|미쳤|쩔)',
    r'(좋|최고|대박|미쳤|쩔).{0,10}ㅅㅂ',
    r'씨발.{0,10}(좋|최고|대박)',
]

POSITIVE_EMOJIS = set('😀😃😄😁😆😅🤣😂😊😇🥰😍🤩😘👍👏🙌💪✨🌟⭐💖💗❤🔥💯🎉👑💎🏆😎🤗🥳')
NEGATIVE_EMOJIS = set('😢😭😤😠😡🤬💔👎🙄😒😞😔😟😣😖😫😩😱🤮🤢')


def analyze_sentiment(text: str) -> tuple:
    """
    맥락 기반 감성 분석
    1. 부정 전환 패턴 체크 (재미없어 ㅋㅋㅋ → 부정)
    2. 긍정적 욕설 패턴 체크 (미친 연기력 → 긍정)
    3. 아이러니 패턴 체크 (어이없어서 웃음 → 부정)
    4. 기본 키워드 분석
    """
    if not text:
        return 'neutral', 0.0
    
    text_lower = text.lower()
    score = 0.0
    
    # === 1단계: 부정 전환 패턴 체크 ===
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, text_lower):
            score -= 0.8
            break
    
    # === 2단계: 아이러니/반어 패턴 ===
    for pattern in IRONY_NEGATIVE_PATTERNS:
        if re.search(pattern, text_lower):
            score -= 0.6
            break
    
    # === 3단계: 긍정적 욕설 컨텍스트 ===
    for pattern in POSITIVE_SWEAR_CONTEXT:
        if re.search(pattern, text_lower):
            score += 1.0
            break
    
    # === 4단계: 이모지 분석 ===
    pos_emoji = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_emoji = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    score += (pos_emoji - neg_emoji) * 0.2
    
    # === 5단계: 키워드 분석 ===
    words = re.findall(r'[가-힣]+|[a-zA-Z]+', text_lower)
    
    pos_count = 0
    neg_count = 0
    
    for word in words:
        if any(p in word for p in POSITIVE_EXPRESSIONS):
            pos_count += 1
        if any(n in word for n in NEGATIVE_EXPRESSIONS):
            neg_count += 1
    
    # 부정 전환 패턴이 없을 때만 긍정 점수 부여
    if score >= 0:  
        score += pos_count * 0.3
    score -= neg_count * 0.4
    
    # === 6단계: 웃음 표현 (맥락에 따라) ===
    laugh = len(re.findall(r'ㅋ{2,}|ㅎ{2,}', text))
    if laugh > 0:
        # 부정 맥락이 없으면 긍정, 있으면 중립 유지
        if score >= 0:
            score += laugh * 0.2
        # 부정 맥락 + 웃음 = 비꼼이므로 점수 유지
    
    # === 7단계: 최종 판정 ===
    if score >= 0.4:
        return 'positive', score
    elif score <= -0.4:
        return 'negative', score
    return 'neutral', score


# =============================================================================
# 핵심 요인 분석
# =============================================================================
def analyze_factors(comments_df: pd.DataFrame) -> dict:
    """긍정/부정 핵심 요인 분석"""
    
    pos_df = comments_df[comments_df['sentiment'] == 'positive']
    neg_df = comments_df[comments_df['sentiment'] == 'negative']
    
    # 긍정 요인 키워드 그룹
    positive_factor_groups = {
        '재미/유머': ['재밌', '웃기', '웃겨', '꿀잼', '핵잼', '유머', '센스', '킬링'],
        '퀄리티/완성도': ['퀄리티', '완성도', '대박', '미쳤', '쩐다', '레전드'],
        '출연자/비주얼': ['예쁘', '이쁘', '잘생', '비주얼', '매력', '귀엽', '귀여'],
        '감동/공감': ['감동', '눈물', '울컥', '공감', '힐링', '따뜻'],
        '기대/응원': ['기대', '응원', '화이팅', '파이팅', '사랑'],
    }
    
    # 부정 요인 키워드 그룹
    negative_factor_groups = {
        '지루/재미없음': ['지루', '노잼', '재미없', '별로', '심심'],
        '실망/기대이하': ['실망', '아쉽', '기대이하', '별로'],
        '불편/불쾌': ['불편', '불쾌', '짜증', '화나', '열받'],
        '퀄리티 문제': ['조잡', '대충', '못', '최악', '망'],
        '광고/상업성': ['광고', '협찬', '뻔한', '돈'],
    }
    
    results = {'positive': [], 'negative': []}
    
    # 긍정 요인 분석
    if len(pos_df) > 0:
        pos_text = ' '.join(pos_df['text'].tolist()).lower()
        factor_scores = {}
        
        for factor, keywords in positive_factor_groups.items():
            count = sum(pos_text.count(kw) for kw in keywords)
            if count > 0:
                factor_scores[factor] = count
        
        # 상위 3개 요인
        sorted_factors = sorted(factor_scores.items(), key=lambda x: -x[1])
        results['positive'] = [f for f, _ in sorted_factors[:3]]
    
    # 부정 요인 분석
    if len(neg_df) > 0:
        neg_text = ' '.join(neg_df['text'].tolist()).lower()
        factor_scores = {}
        
        for factor, keywords in negative_factor_groups.items():
            count = sum(neg_text.count(kw) for kw in keywords)
            if count > 0:
                factor_scores[factor] = count
        
        sorted_factors = sorted(factor_scores.items(), key=lambda x: -x[1])
        results['negative'] = [f for f, _ in sorted_factors[:3]]
    
    return results


# =============================================================================
# 유틸리티
# =============================================================================
def extract_video_id(url: str) -> str:
    if not url:
        return None
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return url if re.match(r'^[a-zA-Z0-9_-]{11}$', url) else None


def format_date(date_str: str) -> str:
    if not date_str or len(date_str) != 8:
        return "정보 없음"
    return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"


def format_number(num) -> str:
    try:
        num = int(num) if num else 0
        if num >= 100000000:
            return f"{num/100000000:.1f}억"
        if num >= 10000:
            return f"{num/10000:.1f}만"
        if num >= 1000:
            return f"{num/1000:.1f}천"
        return f"{num:,}"
    except:
        return "0"


STOPWORDS = {'은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '도', '만', '로', '으로',
             '하고', '그리고', '그런데', '하지만', '그래서', '또', '더', '막', '좀', '이제', '진짜', '너무', '정말', '완전',
             '것', '거', '수', '때', '중', '년', '월', '일', '번', '분', '게', '데', '뭐', '왜', '어떻게',
             '나', '너', '우리', '저', '영상', '댓글', '유튜브', '채널', '구독', '좋아요', '시청',
             'the', 'a', 'an', 'is', 'are', 'to', 'of', 'in', 'for', 'on', 'with', 'this', 'that',
             'i', 'you', 'it', 'and', 'but', 'or', 'so', 'video', 'comment', 'like', 'just'}


def extract_keywords(texts: list, top_n: int = 10) -> list:
    words = []
    for text in texts:
        if not text:
            continue
        text = re.sub(r'http\S+', '', text.lower())
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        tokens = text.split()
        words.extend([t for t in tokens if t not in STOPWORDS and len(t) > 1])
    
    return Counter(words).most_common(top_n)


def generate_insight(video_info, pos_pct, neg_pct, factors, keywords) -> str:
    insights = []
    
    # 전반적 반응
    if pos_pct >= 70:
        insights.append(f"시청자 반응이 매우 긍정적입니다(긍정 {pos_pct:.0f}%). 바이럴 가능성이 높고, 시리즈화나 유사 콘텐츠 기획이 유효합니다.")
    elif pos_pct >= 50:
        insights.append(f"전반적으로 호의적인 반응입니다(긍정 {pos_pct:.0f}%). 개선 포인트를 파악하면 더 높은 만족도를 이끌어낼 수 있습니다.")
    elif neg_pct >= 30:
        insights.append(f"부정적 반응이 상당합니다(부정 {neg_pct:.0f}%). 핵심 불만 요인을 파악하고 대응이 필요합니다.")
    else:
        insights.append(f"반응이 혼재되어 있습니다. 긍정과 부정 요인을 모두 분석해볼 필요가 있습니다.")
    
    # 핵심 요인 기반
    if factors.get('positive'):
        top_factor = factors['positive'][0]
        insights.append(f"긍정 반응의 핵심은 '{top_factor}'입니다. 이 강점을 유지하거나 강화하세요.")
    
    if factors.get('negative'):
        top_factor = factors['negative'][0]
        insights.append(f"부정 반응의 주요 원인은 '{top_factor}'로 보입니다. 개선 또는 해명이 도움이 될 수 있습니다.")
    
    # 키워드 기반
    if keywords:
        top_kw = keywords[0][0]
        insights.append(f"가장 많이 언급된 '{top_kw}'를 중심으로 후속 콘텐츠를 기획해보세요.")
    
    return " ".join(insights)


# =============================================================================
# 데이터 수집
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_video_data(url: str, max_comments: int):
    import yt_dlp
    
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'getcomments': True,
        'extractor_args': {
            'youtube': {
                'max_comments': [str(max_comments)],
                'comment_sort': ['top'],
            }
        }
    }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        if not info:
            return None, []
        
        video_info = {
            'title': info.get('title', '제목 없음'),
            'channel': info.get('channel', info.get('uploader', '채널 정보 없음')),
            'upload_date': format_date(info.get('upload_date', '')),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'total_comments': info.get('comment_count', 0),
        }
        
        raw_comments = info.get('comments') or []
        comments = []
        for c in raw_comments[:max_comments]:
            if c and isinstance(c, dict):
                comments.append({
                    'text': c.get('text', ''),
                    'likes': c.get('like_count', 0) or 0,
                })
        
        return video_info, comments


# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 헤더
    st.markdown('''
    <div class="header">
        <h1>유튜브 댓글 분석기</h1>
        <p>영상 URL을 입력하면 댓글의 감성과 핵심 요인을 분석합니다</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 입력
    url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed"
    )
    
    st.markdown(f'<div class="notice">💡 댓글은 인기순으로 최대 {MAX_COMMENTS}개까지 분석됩니다.</div>', unsafe_allow_html=True)
    
    if st.button("분석 시작", use_container_width=True):
        video_id = extract_video_id(url)
        
        if not video_id:
            st.error("올바른 YouTube URL을 입력해주세요.")
            return
        
        try:
            with st.spinner("댓글을 수집하고 있습니다..."):
                video_info, comments = fetch_video_data(url, MAX_COMMENTS)
            
            if not video_info:
                st.error("영상 정보를 가져올 수 없습니다.")
                return
            
            if not comments:
                st.warning("댓글이 없거나 가져올 수 없습니다.")
                return
            
            with st.spinner("분석 중..."):
                # 감성 분석
                for c in comments:
                    sent, score = analyze_sentiment(c['text'])
                    c['sentiment'] = sent
                    c['score'] = score
                
                df = pd.DataFrame(comments)
                
                # 통계
                total = len(df)
                pos_count = len(df[df['sentiment'] == 'positive'])
                neg_count = len(df[df['sentiment'] == 'negative'])
                neu_count = total - pos_count - neg_count
                
                pos_pct = pos_count / total * 100
                neg_pct = neg_count / total * 100
                neu_pct = neu_count / total * 100
                
                # 키워드
                keywords = extract_keywords([c['text'] for c in comments], 10)
                
                # 요인 분석
                factors = analyze_factors(df)
            
            # ===== 결과 출력 =====
            
            # 영상 정보
            st.markdown('<div class="section-title">영상 정보</div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div class="card">
                <div class="video-title">{video_info.get("title", "")}</div>
                <div class="video-meta">
                    <span class="video-meta-item">👤 {video_info.get("channel", "")}</span>
                    <span class="video-meta-item">📅 {video_info.get("upload_date", "")}</span>
                    <span class="video-meta-item">👁 {format_number(video_info.get("view_count", 0))}</span>
                    <span class="video-meta-item">💬 {format_number(video_info.get("total_comments", 0))}개 중 {total}개 분석</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 감성 분석
            st.markdown('<div class="section-title">감성 분석</div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div class="card">
                <div class="sentiment-bar">
                    <div class="sentiment-pos" style="width:{pos_pct}%"></div>
                    <div class="sentiment-neu" style="width:{neu_pct}%"></div>
                    <div class="sentiment-neg" style="width:{neg_pct}%"></div>
                </div>
                <div class="sentiment-labels">
                    <span class="sentiment-label"><span class="dot dot-pos"></span> 긍정 {pos_pct:.1f}%</span>
                    <span class="sentiment-label"><span class="dot dot-neu"></span> 중립 {neu_pct:.1f}%</span>
                    <span class="sentiment-label"><span class="dot dot-neg"></span> 부정 {neg_pct:.1f}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 키워드
            st.markdown('<div class="section-title">주요 키워드</div>', unsafe_allow_html=True)
            kw_html = ' '.join([f'<span class="keyword-tag"><strong>{kw}</strong> {cnt}</span>' for kw, cnt in keywords[:8]])
            st.markdown(f'<div class="card"><div class="keyword-list">{kw_html}</div></div>', unsafe_allow_html=True)
            
            # 핵심 요인
            st.markdown('<div class="section-title">핵심 요인 분석</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if factors['positive']:
                    factors_text = ', '.join(factors['positive'])
                    st.markdown(f'''
                    <div class="factor-box">
                        <div class="factor-title">😊 긍정 반응 핵심 요인</div>
                        <div class="factor-desc">{factors_text}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                    <div class="factor-box">
                        <div class="factor-title">😊 긍정 반응 핵심 요인</div>
                        <div class="factor-desc">분석된 요인 없음</div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            with col2:
                if factors['negative']:
                    factors_text = ', '.join(factors['negative'])
                    st.markdown(f'''
                    <div class="factor-box">
                        <div class="factor-title">😞 부정 반응 핵심 요인</div>
                        <div class="factor-desc">{factors_text}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                    <div class="factor-box">
                        <div class="factor-title">😞 부정 반응 핵심 요인</div>
                        <div class="factor-desc">부정 댓글이 거의 없습니다</div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            # 대표 댓글
            st.markdown('<div class="section-title">대표 댓글</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            pos_df = df[df['sentiment'] == 'positive']
            neg_df = df[df['sentiment'] == 'negative']
            
            with col1:
                st.markdown('<div class="comment-section-title">👍 긍정 댓글</div>', unsafe_allow_html=True)
                if len(pos_df) > 0:
                    for _, row in pos_df.nlargest(3, 'likes').iterrows():
                        text = row['text'][:100] + ('...' if len(row['text']) > 100 else '')
                        st.markdown(f'''
                        <div class="comment-item positive">
                            <div class="comment-text">{text}</div>
                            <div class="comment-meta">좋아요 {int(row["likes"]):,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="comment-item">긍정 댓글 없음</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="comment-section-title">👎 부정 댓글</div>', unsafe_allow_html=True)
                if len(neg_df) > 0:
                    for _, row in neg_df.nlargest(3, 'likes').iterrows():
                        text = row['text'][:100] + ('...' if len(row['text']) > 100 else '')
                        st.markdown(f'''
                        <div class="comment-item negative">
                            <div class="comment-text">{text}</div>
                            <div class="comment-meta">좋아요 {int(row["likes"]):,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="comment-item">부정 댓글이 거의 없습니다 🎉</div>', unsafe_allow_html=True)
            
            # 베스트 댓글
            st.markdown('<div class="section-title">베스트 댓글 TOP 5</div>', unsafe_allow_html=True)
            
            for i, (_, row) in enumerate(df.nlargest(5, 'likes').iterrows(), 1):
                text = row['text'][:120] + ('...' if len(row['text']) > 120 else '')
                st.markdown(f'''
                <div class="comment-item best">
                    <div class="comment-text"><strong>#{i}</strong> {text}</div>
                    <div class="comment-meta">좋아요 {int(row["likes"]):,}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 종합 인사이트
            st.markdown('<div class="section-title">종합 인사이트</div>', unsafe_allow_html=True)
            insight = generate_insight(video_info, pos_pct, neg_pct, factors, keywords)
            st.markdown(f'''
            <div class="insight-box">
                <div class="insight-title">💡 분석 요약</div>
                <div class="insight-text">{insight}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 푸터
            st.markdown('<div class="footer">유튜브 댓글 분석기 v2.0</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
