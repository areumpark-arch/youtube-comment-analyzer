#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 인사이트 분석기 v5.0
================================
깔끔한 디자인 버전
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from typing import List, Tuple, Optional
from collections import Counter

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
# 전체 CSS 스타일
# =============================================================================
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #f5f7fa;
    }
    
    /* 메인 컨테이너 */
    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1200px !important;
    }
    
    /* 헤더 영역 */
    .header-container {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(30, 58, 95, 0.3);
    }
    .header-title {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 0;
    }
    
    /* 입력 영역 */
    .input-container {
        background: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    /* 카드 스타일 */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
        height: 100%;
    }
    .card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .card-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
        line-height: 1.2;
    }
    .card-value.positive { color: #059669; }
    .card-value.negative { color: #dc2626; }
    
    /* 영상 정보 카드 */
    .video-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1.5rem;
        display: flex;
        gap: 1.5rem;
        align-items: flex-start;
    }
    .video-info h2 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 0.5rem 0;
        line-height: 1.4;
    }
    .video-meta {
        color: #64748b;
        font-size: 0.9rem;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* 인사이트 박스 */
    .insight-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1e3a5f;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .insight-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .insight-desc {
        font-size: 0.95rem;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 0.5rem;
    }
    .insight-action {
        font-size: 0.85rem;
        color: #2d5a87;
        font-style: italic;
    }
    
    /* 댓글 박스 */
    .comment-card {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #cbd5e1;
    }
    .comment-card.positive {
        border-left-color: #059669;
        background: #f0fdf4;
    }
    .comment-card.negative {
        border-left-color: #dc2626;
        background: #fef2f2;
    }
    .comment-text {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }
    .comment-likes {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    /* 액션 아이템 */
    .action-item {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .action-num {
        background: #1e3a5f;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 600;
        flex-shrink: 0;
    }
    .action-text {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.5;
    }
    
    /* 차트 컨테이너 */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }
    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 2rem;
    }
    
    /* Streamlit 기본 요소 숨기기/수정 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 10px;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.4);
    }
    
    /* 입력 필드 */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1e3a5f;
        box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
    }
    
    /* 메트릭 스타일 수정 */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #64748b;
    }
    
    /* 프로그레스 바 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1e3a5f, #2d5a87);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 설정 & 상수
# =============================================================================
CONFIG = {
    "max_comments": 800,
    "top_keywords_count": 15,
}

STOPWORDS = set([
    '은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '도', '만', '로', '으로',
    '하고', '그리고', '그런데', '하지만', '그래서', '그러나', '또한', '및', '등',
    '나', '너', '우리', '저', '이것', '저것', '그것', '여기', '저기', '거기',
    '하다', '되다', '있다', '없다', '같다', '보다', '알다', '싶다', '주다',
    '하는', '하면', '해서', '했다', '한다', '할', '함', '되는', '되면', '됐다', '된다',
    '있는', '있으면', '있고', '있어서', '있었다', '있을', '있음',
    '것', '거', '수', '때', '중', '내', '년', '월', '일', '번', '분',
    '영상', '댓글', '동영상', '유튜브', '채널', '구독', '좋아요', '시청',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'we', 'they',
    'this', 'that', 'and', 'but', 'or', 'so', 'if',
    'video', 'comment', 'youtube', 'channel', 'subscribe',
])

POSITIVE_WORDS = {
    '좋다', '좋아', '좋네', '좋은', '좋았', '좋음', '좋아요', '좋습니다',
    '최고', '최고다', '최고야', '최고예요', '최고임', '최곱니다',
    '대박', '대박이다', '대박이야', '대박이네',
    '멋지다', '멋져', '멋있다', '멋있어', '멋짐', '멋진',
    '예쁘다', '예뻐', '예쁨', '이쁘다', '이뻐',
    '사랑', '사랑해', '사랑해요', '사랑합니다', '사랑스럽',
    '감사', '감사해요', '감사합니다', '고마워', '고맙습니다',
    '행복', '행복해', '기쁘다', '즐겁다', '즐거워',
    '기대', '기대된다', '기대돼', '기대됩니다',
    '응원', '응원해', '화이팅', '파이팅', '힘내',
    '훌륭', '완벽', '감동', '설렘', '설레',
    '재밌', '재밌다', '재미있', '웃기다', '웃겨', '웃김',
    '힐링', '귀엽', '귀여워', '깜찍',
    '잘생', '잘생겼', '존잘', '존예', '개예쁨',
    '짱', '쩔어', '쩐다', '미쳤', '미쳤다', '미침',
    '대단', '놀랍', '신기', '레전드', '레전더리',
    '인정', '추천', '갓', '존경', '리스펙',
    '천재', '아름답', '환상적', '최애',
    '역시', '믿고보는', '찐', '꿀잼', '핵잼', '존잼',
    '소름', '감탄', '눈물', '울컥', '공감',
    'good', 'great', 'best', 'love', 'like', 'amazing', 'awesome',
    'beautiful', 'excellent', 'fantastic', 'nice', 'perfect', 'happy',
    'incredible', 'brilliant', 'wow', 'omg', 'fire', 'goat',
    'queen', 'king', 'icon', 'slay', 'legend',
}

NEGATIVE_WORDS = {
    '싫다', '싫어', '싫음', '별로', '별루',
    '최악', '최악이다', '실망', '실망했',
    '짜증', '짜증나', '짜증남',
    '화나', '화남', '답답', '불쾌',
    '슬프', '슬퍼', '우울',
    '아쉽', '아쉬워', '걱정', '불안',
    '힘들', '힘들다', '피곤',
    '나쁘', '나빠', '못하', '못함',
    '후회', '혐오', '역겹',
    '지루', '노잼', '재미없', '망했', '망함',
    '쓰레기', '불편', '비추',
    'bad', 'worst', 'hate', 'terrible', 'awful',
    'sad', 'angry', 'disappointed', 'boring',
    'fail', 'trash', 'cringe', 'mid',
}

POSITIVE_EMOJIS = set('😀😃😄😁😆😅🤣😂😊😇🥰😍🤩😘👍👏🙌💪✨🌟⭐💖💗❤🧡💛💚💙💜💝🔥💯🎉👑💎🏆😎🤗🥳❤️')
NEGATIVE_EMOJIS = set('😢😭😤😠😡🤬💔👎🙄😒😞😔😟🙁😣😖😫😩😱🤮🤢')

# =============================================================================
# 유틸리티 함수
# =============================================================================
def extract_video_id(url: str) -> Optional[str]:
    if not url:
        return None
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return None

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def preprocess_for_keywords(text: str) -> str:
    text = clean_text(text)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = text.lower()
    text = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', ' ', text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return ' '.join(tokens)

def format_date(date_str: str) -> str:
    if not date_str or len(date_str) != 8:
        return "날짜 정보 없음"
    try:
        return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
    except:
        return str(date_str)

def format_number(num) -> str:
    try:
        num = int(num) if num else 0
        if num >= 100000000:
            return f"{num/100000000:.1f}억"
        elif num >= 10000:
            return f"{num/10000:.1f}만"
        elif num >= 1000:
            return f"{num/1000:.1f}천"
        return f"{num:,}"
    except:
        return "0"

# =============================================================================
# 댓글 수집
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def collect_comments(url: str, max_comments: int):
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp 라이브러리가 필요합니다.")
    
    ydl_opts = {
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None, []
            
            video_info = {
                'video_id': info.get('id', ''),
                'title': info.get('title', '제목 없음'),
                'channel': info.get('channel', info.get('uploader', '채널 정보 없음')),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'comment_count': info.get('comment_count', 0),
                'upload_date': format_date(info.get('upload_date', '')),
            }
            
            raw_comments = info.get('comments') or []
            
            if not raw_comments:
                return video_info, []
            
            comments = []
            for i, c in enumerate(raw_comments):
                if i >= max_comments:
                    break
                if c and isinstance(c, dict):
                    comments.append({
                        'text': c.get('text', ''),
                        'like_count': c.get('like_count', 0) or 0,
                        'author': c.get('author', ''),
                    })
            
            return video_info, comments
            
    except Exception as e:
        raise Exception(f"영상 정보를 가져올 수 없습니다: {str(e)}")

# =============================================================================
# 감성 분석
# =============================================================================
def analyze_sentiment(text: str) -> Tuple[str, float]:
    if not text or not isinstance(text, str):
        return 'neutral', 0.0
    
    text_lower = text.lower()
    score = 0.0
    
    pos_emoji = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_emoji = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    if pos_emoji + neg_emoji > 0:
        score += (pos_emoji - neg_emoji) / (pos_emoji + neg_emoji + 1) * 1.5
    
    words = set(re.findall(r'[가-힣]+|[a-z]+', text_lower))
    pos_count = sum(1 for w in words if any(pw in w or w in pw for pw in POSITIVE_WORDS))
    neg_count = sum(1 for w in words if any(nw in w or w in nw for nw in NEGATIVE_WORDS))
    if pos_count + neg_count > 0:
        score += (pos_count - neg_count) / (pos_count + neg_count + 0.5)
    
    if re.search(r'ㅋ{2,}|ㅎ{2,}', text):
        score += 0.3
    if re.search(r'ㅡㅡ|;;', text):
        score -= 0.3
    if text.count('!') >= 2:
        score += 0.2
    
    if score > 0.1:
        return 'positive', min(score, 1.0)
    elif score < -0.1:
        return 'negative', max(score, -1.0)
    return 'neutral', score

# =============================================================================
# 키워드 추출
# =============================================================================
def extract_keywords(texts: List[str], top_n: int = 15) -> List[Tuple[str, int]]:
    all_words = []
    for text in texts:
        if text:
            processed = preprocess_for_keywords(str(text))
            words = processed.split()
            all_words.extend([w for w in words if len(w) > 1])
    
    if not all_words:
        return []
    
    counter = Counter(all_words)
    return counter.most_common(top_n)

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 헤더
    st.markdown('''
    <div class="header-container">
        <h1 class="header-title">📊 유튜브 댓글 분석기</h1>
        <p class="header-subtitle">영상 URL을 입력하면 댓글 인사이트를 분석합니다</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # URL 입력
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        url = st.text_input(
            "YouTube URL을 입력하세요",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed"
        )
        analyze_btn = st.button("🔍 분석 시작", use_container_width=True)
    
    # 분석 실행
    if analyze_btn and url:
        video_id = extract_video_id(url)
        
        if not video_id:
            st.error("❌ 유효하지 않은 YouTube URL입니다.")
            return
        
        try:
            status = st.empty()
            progress = st.progress(0)
            
            status.info("📥 영상 정보 및 댓글을 수집하고 있습니다... (1~2분 소요)")
            progress.progress(10)
            
            video_info, comments = collect_comments(url, CONFIG["max_comments"])
            progress.progress(40)
            
            if video_info is None:
                st.error("❌ 영상 정보를 가져올 수 없습니다.")
                return
            
            if not comments:
                st.warning("⚠️ 댓글이 없거나 가져올 수 없습니다.")
                return
            
            status.info("🔍 감성 분석 중...")
            progress.progress(60)
            
            df = pd.DataFrame(comments)
            results = [analyze_sentiment(str(text)) for text in df['text'].fillna('')]
            df['sentiment_label'] = [r[0] for r in results]
            df['sentiment_score'] = [r[1] for r in results]
            
            status.info("🔑 키워드 분석 중...")
            progress.progress(80)
            
            keywords = extract_keywords(df['text'].tolist(), CONFIG["top_keywords_count"])
            
            progress.progress(100)
            status.empty()
            progress.empty()
            
            # =================================================================
            # 결과 표시
            # =================================================================
            
            # 영상 정보
            col1, col2 = st.columns([1, 2.5])
            with col1:
                if video_info.get('thumbnail'):
                    st.image(video_info['thumbnail'], use_container_width=True)
            with col2:
                st.markdown(f"### {video_info.get('title', '제목 없음')}")
                st.markdown(f"**{video_info.get('channel', '')}** · 업로드: {video_info.get('upload_date', 'N/A')}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 핵심 지표
            total = len(df)
            pos_count = int((df['sentiment_label'] == 'positive').sum())
            neu_count = int((df['sentiment_label'] == 'neutral').sum())
            neg_count = int((df['sentiment_label'] == 'negative').sum())
            pos_pct = pos_count / total * 100 if total > 0 else 0
            neg_pct = neg_count / total * 100 if total > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 분석 댓글", f"{total:,}개")
            with col2:
                st.metric("😊 긍정률", f"{pos_pct:.1f}%")
            with col3:
                st.metric("👁️ 조회수", format_number(video_info.get('view_count', 0)))
            with col4:
                st.metric("👍 좋아요", format_number(video_info.get('like_count', 0)))
            
            st.markdown('<div class="section-title">📊 분석 결과</div>', unsafe_allow_html=True)
            
            # 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">감성 분포</div>', unsafe_allow_html=True)
                
                chart_df = pd.DataFrame({
                    '감성': ['😊 긍정', '😐 중립', '😞 부정'],
                    '댓글 수': [pos_count, neu_count, neg_count]
                }).set_index('감성')
                st.bar_chart(chart_df, color=['#1e3a5f'])
                
                st.caption(f"긍정 {pos_count:,} ({pos_pct:.1f}%) · 중립 {neu_count:,} · 부정 {neg_count:,} ({neg_pct:.1f}%)")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown('<div class="chart-title">핵심 키워드 TOP 10</div>', unsafe_allow_html=True)
                
                if keywords:
                    kw_df = pd.DataFrame(keywords[:10], columns=['키워드', '언급']).set_index('키워드')
                    st.bar_chart(kw_df, color=['#2d5a87'])
                else:
                    st.info("키워드 데이터 없음")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 인사이트
            st.markdown('<div class="section-title">💡 핵심 인사이트</div>', unsafe_allow_html=True)
            
            top_liked = df.nlargest(min(20, len(df)), 'like_count')
            top_pos_ratio = (top_liked['sentiment_label'] == 'positive').sum() / max(len(top_liked), 1) * 100
            
            if pos_pct > 60:
                st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">🌟 강력한 팬덤 기반의 긍정적 바이럴 잠재력</div>
                    <div class="insight-desc">전체 댓글의 <b>{pos_pct:.0f}%</b>가 긍정적 반응입니다. 좋아요 상위 댓글의 <b>{top_pos_ratio:.0f}%</b>가 긍정인 점은 커뮤니티 내 여론 주도층이 우호적이라는 신호입니다.</div>
                    <div class="insight-action">→ UGC 캠페인, 팬 참여형 챌린지 등 "팬이 홍보대사가 되는" 전략 권장</div>
                </div>
                ''', unsafe_allow_html=True)
            elif pos_pct > 40:
                st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">📈 호의적이나 열성 팬 전환이 필요한 시점</div>
                    <div class="insight-desc">긍정 비율 <b>{pos_pct:.0f}%</b>는 좋은 수치이나, "좋아하지만 굳이 찾아보진 않는" 가벼운 관심층일 가능성이 있습니다.</div>
                    <div class="insight-action">→ 정기적 터치포인트(비하인드, 팬서비스 콘텐츠)로 관계 깊이를 더해야 함</div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">📊 시청자 반응 패턴 분석 필요</div>
                    <div class="insight-desc">긍정 반응이 <b>{pos_pct:.0f}%</b>입니다. 시청자들의 구체적인 피드백을 분석해볼 필요가 있습니다.</div>
                    <div class="insight-action">→ 댓글 키워드와 부정 의견을 참고하여 개선점 파악</div>
                </div>
                ''', unsafe_allow_html=True)
            
            if neg_pct > 20:
                st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">⚠️ 부정 여론 파악 필요</div>
                    <div class="insight-desc">부정 반응이 <b>{neg_pct:.0f}%</b>로 무시할 수 없는 수준입니다. 핵심 원인 파악이 필요합니다.</div>
                    <div class="insight-action">→ 부정 댓글 키워드 분석 후 해명/개선이 필요한 영역 식별</div>
                </div>
                ''', unsafe_allow_html=True)
            
            if keywords:
                top_kws = ', '.join([kw for kw, _ in keywords[:5]])
                st.markdown(f'''
                <div class="insight-card">
                    <div class="insight-title">🔑 시청자 언어: "{keywords[0][0]}"</div>
                    <div class="insight-desc">가장 많이 언급된 키워드는 <b>"{top_kws}"</b>입니다. 이 단어들이 시청자들의 인식을 보여줍니다.</div>
                    <div class="insight-action">→ 마케팅 메시지, 썸네일, 제목에 "{keywords[0][0]}" 키워드 활용 권장</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 대표 댓글
            st.markdown('<div class="section-title">💬 주요 댓글</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👍 긍정 반응 TOP 3**")
                top_pos = df[df['sentiment_label'] == 'positive'].nlargest(3, 'like_count')
                if len(top_pos) > 0:
                    for _, row in top_pos.iterrows():
                        text = str(row['text'])[:150] + ('...' if len(str(row['text'])) > 150 else '')
                        likes = int(row['like_count']) if pd.notna(row['like_count']) else 0
                        st.markdown(f'''
                        <div class="comment-card positive">
                            <div class="comment-text">"{text}"</div>
                            <div class="comment-likes">👍 {likes:,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info("긍정 댓글 없음")
            
            with col2:
                st.markdown("**👎 부정/우려 TOP 3**")
                top_neg = df[df['sentiment_label'] == 'negative'].nlargest(3, 'like_count')
                if len(top_neg) > 0:
                    for _, row in top_neg.iterrows():
                        text = str(row['text'])[:150] + ('...' if len(str(row['text'])) > 150 else '')
                        likes = int(row['like_count']) if pd.notna(row['like_count']) else 0
                        st.markdown(f'''
                        <div class="comment-card negative">
                            <div class="comment-text">"{text}"</div>
                            <div class="comment-likes">👍 {likes:,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.success("🎉 부정 댓글이 거의 없습니다!")
            
            # 액션 아이템
            st.markdown('<div class="section-title">🎯 액션 아이템</div>', unsafe_allow_html=True)
            
            actions = []
            if pos_pct > 50:
                actions.append("팬 참여형 콘텐츠(Q&A, 투표, 챌린지) 기획으로 engagement 극대화")
            if neg_pct > 15:
                actions.append("부정 댓글 패턴 분석 후 FAQ/공지 형태의 선제적 커뮤니케이션")
            if keywords:
                actions.append(f'"{keywords[0][0]}" 키워드 활용한 썸네일/제목 A/B 테스트')
            actions.append("열성 팬(반복 댓글러) 식별 후 앰배서더 프로그램 타겟팅")
            actions.append("댓글 반응 좋은 시간대 분석하여 업로드 스케줄 최적화")
            
            for i, action in enumerate(actions[:5], 1):
                st.markdown(f'''
                <div class="action-item">
                    <div class="action-num">{i}</div>
                    <div class="action-text">{action}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 푸터
            st.markdown('<div class="footer">📊 유튜브 댓글 분석기 v5.0 | 마케터를 위한 인사이트 도구</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("💡 올바른 YouTube URL인지, 공개 영상인지 확인해주세요.")

if __name__ == "__main__":
    main()
