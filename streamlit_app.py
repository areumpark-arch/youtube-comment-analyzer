#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 인사이트 분석기 v4.0
================================
Streamlit Cloud 배포용 (한글 버전)
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from typing import List, Tuple, Optional
from collections import Counter

# =============================================================================
# 페이지 설정 (가장 먼저!)
# =============================================================================
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# CSS 스타일
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background: #f8fafc;
        border-left: 4px solid #1e3a5f;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .insight-title {
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    .insight-desc {
        color: #334155;
        margin-bottom: 0.5rem;
    }
    .insight-action {
        font-style: italic;
        color: #2d5a87;
        font-size: 0.9rem;
    }
    .comment-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #7ba3cc;
    }
    .comment-box.positive { border-left-color: #2d5a87; }
    .comment-box.negative { border-left-color: #8b4557; }
    .stButton>button {
        background: #1e3a5f;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background: #2d5a87;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 설정
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

# =============================================================================
# 유틸리티 함수
# =============================================================================
def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 비디오 ID 추출"""
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
    """텍스트 정리"""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def preprocess_for_keywords(text: str) -> str:
    """키워드 추출용 전처리"""
    text = clean_text(text)
    # 이모지 제거
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
    """날짜 포맷팅"""
    if not date_str or len(date_str) != 8:
        return "날짜 정보 없음"
    try:
        return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
    except:
        return str(date_str)

def format_number(num) -> str:
    """숫자 포맷팅"""
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
# 댓글 수집 함수
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def collect_comments(url: str, max_comments: int):
    """YouTube 댓글 수집"""
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

def analyze_sentiment(text: str) -> Tuple[str, float]:
    """감성 분석"""
    if not text or not isinstance(text, str):
        return 'neutral', 0.0
    
    text_lower = text.lower()
    score = 0.0
    
    # 이모지 분석
    pos_emoji = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_emoji = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    if pos_emoji + neg_emoji > 0:
        score += (pos_emoji - neg_emoji) / (pos_emoji + neg_emoji + 1) * 1.5
    
    # 단어 분석
    words = set(re.findall(r'[가-힣]+|[a-z]+', text_lower))
    pos_count = sum(1 for w in words if any(pw in w or w in pw for pw in POSITIVE_WORDS))
    neg_count = sum(1 for w in words if any(nw in w or w in nw for nw in NEGATIVE_WORDS))
    if pos_count + neg_count > 0:
        score += (pos_count - neg_count) / (pos_count + neg_count + 0.5)
    
    # 패턴 분석
    if re.search(r'ㅋ{2,}|ㅎ{2,}', text):
        score += 0.3
    if re.search(r'ㅡㅡ|;;', text):
        score -= 0.3
    if text.count('!') >= 2:
        score += 0.2
    
    # 판정
    if score > 0.1:
        return 'positive', min(score, 1.0)
    elif score < -0.1:
        return 'negative', max(score, -1.0)
    return 'neutral', score

# =============================================================================
# 키워드 추출
# =============================================================================
def extract_keywords(texts: List[str], top_n: int = 15) -> List[Tuple[str, int]]:
    """빈도 기반 키워드 추출"""
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
    st.markdown('<h1 class="main-header">📊 유튜브 댓글 분석기</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">영상 URL을 입력하면 댓글 인사이트를 분석합니다</p>', unsafe_allow_html=True)
    
    # URL 입력
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed"
        )
        analyze_btn = st.button("🔍 분석 시작", use_container_width=True)
    
    st.markdown("---")
    
    # 분석 실행
    if analyze_btn and url:
        video_id = extract_video_id(url)
        
        if not video_id:
            st.error("❌ 유효하지 않은 YouTube URL입니다. 올바른 URL을 입력해주세요.")
            st.info("예시: https://www.youtube.com/watch?v=XXXXXXXXXXX")
            return
        
        try:
            # 진행 상태 표시
            status = st.empty()
            progress = st.progress(0)
            
            status.text("📥 영상 정보 및 댓글을 수집하고 있습니다... (1~2분 소요)")
            progress.progress(10)
            
            # 댓글 수집
            video_info, comments = collect_comments(url, CONFIG["max_comments"])
            progress.progress(40)
            
            if video_info is None:
                st.error("❌ 영상 정보를 가져올 수 없습니다.")
                return
            
            if not comments:
                st.warning("⚠️ 댓글이 없거나 댓글을 가져올 수 없습니다.")
                st.info("💡 댓글이 비활성화된 영상이거나, 비공개 영상일 수 있습니다.")
                
                # 영상 정보만이라도 표시
                st.markdown("### 📺 영상 정보")
                st.markdown(f"**제목:** {video_info.get('title', 'N/A')}")
                st.markdown(f"**채널:** {video_info.get('channel', 'N/A')}")
                st.markdown(f"**업로드:** {video_info.get('upload_date', 'N/A')}")
                return
            
            status.text("🔍 감성 분석 중...")
            progress.progress(60)
            
            # DataFrame 생성
            df = pd.DataFrame(comments)
            
            # 감성 분석
            results = [analyze_sentiment(str(text)) for text in df['text'].fillna('')]
            df['sentiment_label'] = [r[0] for r in results]
            df['sentiment_score'] = [r[1] for r in results]
            
            status.text("🔑 키워드 분석 중...")
            progress.progress(80)
            
            # 키워드 추출
            keywords = extract_keywords(df['text'].tolist(), CONFIG["top_keywords_count"])
            
            progress.progress(100)
            status.empty()
            progress.empty()
            
            # =================================================================
            # 결과 표시
            # =================================================================
            
            # 영상 정보 헤더
            col1, col2 = st.columns([1, 3])
            with col1:
                thumbnail = video_info.get('thumbnail', '')
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)
            with col2:
                st.markdown(f"### {video_info.get('title', '제목 없음')}")
                st.markdown(f"**{video_info.get('channel', '채널 정보 없음')}** · 업로드: {video_info.get('upload_date', 'N/A')}")
            
            # 핵심 지표
            total = len(df)
            pos_count = int((df['sentiment_label'] == 'positive').sum())
            neu_count = int((df['sentiment_label'] == 'neutral').sum())
            neg_count = int((df['sentiment_label'] == 'negative').sum())
            pos_pct = pos_count / total * 100 if total > 0 else 0
            neg_pct = neg_count / total * 100 if total > 0 else 0
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 분석 댓글", f"{total:,}개")
            col2.metric("😊 긍정률", f"{pos_pct:.1f}%")
            col3.metric("👁️ 조회수", format_number(video_info.get('view_count', 0)))
            col4.metric("👍 좋아요", format_number(video_info.get('like_count', 0)))
            
            st.markdown("---")
            
            # 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 감성 분포")
                chart_df = pd.DataFrame({
                    '감성': ['😊 긍정', '😐 중립', '😞 부정'],
                    '댓글 수': [pos_count, neu_count, neg_count]
                })
                st.bar_chart(chart_df.set_index('감성'), color=['#2d5a87'])
                st.caption(f"긍정 {pos_count:,}개 ({pos_pct:.1f}%) · 중립 {neu_count:,}개 · 부정 {neg_count:,}개 ({neg_pct:.1f}%)")
            
            with col2:
                st.markdown("#### 🔑 핵심 키워드 TOP 10")
                if keywords:
                    kw_df = pd.DataFrame(keywords[:10], columns=['키워드', '언급 횟수'])
                    st.bar_chart(kw_df.set_index('키워드'), color=['#1e3a5f'])
                else:
                    st.info("키워드를 추출할 수 없습니다.")
            
            st.markdown("---")
            
            # 인사이트
            st.markdown("### 💡 핵심 인사이트")
            
            # 좋아요 상위 댓글의 긍정 비율
            top_liked = df.nlargest(min(20, len(df)), 'like_count')
            top_pos_ratio = (top_liked['sentiment_label'] == 'positive').sum() / max(len(top_liked), 1) * 100
            
            if pos_pct > 60:
                st.markdown(f'''
                <div class="insight-box">
                    <div class="insight-title">🌟 강력한 팬덤 기반의 긍정적 바이럴 잠재력</div>
                    <p class="insight-desc">전체 댓글의 <b>{pos_pct:.0f}%</b>가 긍정적 반응입니다. 좋아요 상위 댓글의 <b>{top_pos_ratio:.0f}%</b>가 긍정인 점은 커뮤니티 내 여론 주도층이 우호적이라는 강력한 신호입니다.</p>
                    <p class="insight-action">→ UGC 캠페인, 팬 참여형 챌린지 등 "팬이 홍보대사가 되는" 전략이 효과적</p>
                </div>
                ''', unsafe_allow_html=True)
            elif pos_pct > 40:
                st.markdown(f'''
                <div class="insight-box">
                    <div class="insight-title">📊 호의적이나 열성 팬 전환이 필요한 시점</div>
                    <p class="insight-desc">긍정 비율 <b>{pos_pct:.0f}%</b>는 좋은 수치이나, "좋아하지만 굳이 찾아보진 않는" 가벼운 관심층일 가능성이 있습니다.</p>
                    <p class="insight-action">→ 정기적 터치포인트(비하인드, 팬서비스 콘텐츠)로 관계 깊이를 더해야 함</p>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="insight-box">
                    <div class="insight-title">📊 시청자 반응 분석</div>
                    <p class="insight-desc">긍정 반응이 <b>{pos_pct:.0f}%</b>입니다. 시청자들의 구체적인 반응 패턴을 분석해볼 필요가 있습니다.</p>
                    <p class="insight-action">→ 댓글 키워드와 부정 의견을 참고하여 개선점 파악</p>
                </div>
                ''', unsafe_allow_html=True)
            
            if neg_pct > 20:
                st.markdown(f'''
                <div class="insight-box">
                    <div class="insight-title">⚠️ 부정 여론 파악 필요</div>
                    <p class="insight-desc">부정 반응이 <b>{neg_pct:.0f}%</b>로 무시할 수 없는 수준입니다. "왜" 부정적인지 핵심 원인 파악이 필요합니다.</p>
                    <p class="insight-action">→ 부정 댓글 키워드 분석 후 해명/개선이 필요한 영역 식별</p>
                </div>
                ''', unsafe_allow_html=True)
            
            if keywords:
                top_kws = ', '.join([kw for kw, _ in keywords[:5]])
                st.markdown(f'''
                <div class="insight-box">
                    <div class="insight-title">🔑 시청자 언어: "{keywords[0][0]}"</div>
                    <p class="insight-desc">가장 많이 언급된 키워드는 <b>"{top_kws}"</b>입니다. 이 단어들은 시청자들이 콘텐츠를 어떻게 인식하는지 보여줍니다.</p>
                    <p class="insight-action">→ 마케팅 메시지, 썸네일, 제목에 "{keywords[0][0]}" 키워드 활용 권장</p>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 대표 댓글
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 👍 긍정 반응 TOP 3")
                top_pos = df[df['sentiment_label'] == 'positive'].nlargest(3, 'like_count')
                if len(top_pos) > 0:
                    for _, row in top_pos.iterrows():
                        text = str(row['text'])[:150]
                        if len(str(row['text'])) > 150:
                            text += '...'
                        likes = int(row['like_count']) if pd.notna(row['like_count']) else 0
                        st.markdown(f'''
                        <div class="comment-box positive">
                            <p>"{text}"</p>
                            <small>👍 {likes:,}</small>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info("긍정 댓글이 없습니다.")
            
            with col2:
                st.markdown("#### 👎 부정/우려 TOP 3")
                top_neg = df[df['sentiment_label'] == 'negative'].nlargest(3, 'like_count')
                if len(top_neg) > 0:
                    for _, row in top_neg.iterrows():
                        text = str(row['text'])[:150]
                        if len(str(row['text'])) > 150:
                            text += '...'
                        likes = int(row['like_count']) if pd.notna(row['like_count']) else 0
                        st.markdown(f'''
                        <div class="comment-box negative">
                            <p>"{text}"</p>
                            <small>👍 {likes:,}</small>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.success("부정 댓글이 거의 없습니다! 🎉")
            
            st.markdown("---")
            
            # 액션 아이템
            st.markdown("### 🎯 액션 아이템")
            
            action_num = 1
            if pos_pct > 50:
                st.markdown(f"**{action_num}.** 팬 참여형 콘텐츠(Q&A, 투표, 챌린지) 기획으로 engagement 극대화")
                action_num += 1
            if neg_pct > 15:
                st.markdown(f"**{action_num}.** 부정 댓글 패턴 분석 후 FAQ/공지 형태의 선제적 커뮤니케이션")
                action_num += 1
            if keywords:
                st.markdown(f"**{action_num}.** \"{keywords[0][0]}\" 키워드 활용한 썸네일/제목 A/B 테스트")
                action_num += 1
            st.markdown(f"**{action_num}.** 열성 팬(반복 댓글러) 식별 후 앰배서더 프로그램 타겟팅")
            action_num += 1
            st.markdown(f"**{action_num}.** 댓글 반응 좋은 시간대 분석하여 업로드 스케줄 최적화")
            
            st.markdown("---")
            st.caption("📊 유튜브 댓글 분석기 v4.0 | 마케터를 위한 인사이트 도구")
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("💡 아래 사항을 확인해주세요:")
            st.markdown("""
            - YouTube URL이 올바른지 확인
            - 영상이 공개 상태인지 확인
            - 댓글이 허용된 영상인지 확인
            - 잠시 후 다시 시도
            """)

# =============================================================================
# 실행
# =============================================================================
if __name__ == "__main__":
    main()