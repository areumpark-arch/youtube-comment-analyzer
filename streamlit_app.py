#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 분석기 v1.0 (Clean Build)
=====================================
핵심 기능만 포함한 안정적인 버전
"""

import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import datetime

# =============================================================================
# 설정
# =============================================================================
MAX_COMMENTS = 500  # 댓글 수집 상한선

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# 스타일
# =============================================================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
    }
    .main-header h1 {
        color: #1a1a2e;
        font-size: 1.8rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #666;
        font-size: 0.95rem;
    }
    
    .info-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .info-row {
        display: flex;
        padding: 0.4rem 0;
        border-bottom: 1px solid #eee;
    }
    .info-row:last-child { border-bottom: none; }
    .info-label {
        color: #666;
        min-width: 120px;
        font-size: 0.9rem;
    }
    .info-value {
        color: #1a1a2e;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #eee;
    }
    
    .comment-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #ddd;
    }
    .comment-box.positive { border-left-color: #2ecc71; background: #f0fff4; }
    .comment-box.negative { border-left-color: #e74c3c; background: #fff5f5; }
    .comment-box.best { border-left-color: #3498db; background: #f0f8ff; }
    
    .comment-text {
        color: #333;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 0.3rem;
    }
    .comment-meta {
        color: #888;
        font-size: 0.8rem;
    }
    
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-top: 1rem;
    }
    .insight-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .insight-text {
        font-size: 0.9rem;
        line-height: 1.6;
        opacity: 0.95;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #666;
    }
    
    #MainMenu, footer, .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 감성 분석 사전
# =============================================================================
POSITIVE_WORDS = {
    # 기본 긍정
    '좋아', '좋다', '좋네', '좋은', '좋았', '좋음', '좋아요', '좋습니다',
    '최고', '최고다', '최고야', '최고예요', '최고임', '최곱니다',
    '대박', '대박이다', '대박이야', '대박이네',
    '멋지', '멋져', '멋있', '멋짐', '멋진',
    '예쁘', '예뻐', '예쁜', '이쁘', '이뻐', '이쁜',
    '귀엽', '귀여워', '귀여운', '깜찍',
    '사랑', '사랑해', '사랑스럽',
    '감사', '감사해', '고마워', '고맙',
    '행복', '기쁘', '즐거', '즐겁',
    '훌륭', '완벽', '감동', '감탄',
    '재밌', '재미있', '웃기', '웃긴', '웃겨',
    '힐링', '편안', '따뜻',
    # 강조/감탄 긍정
    '짱', '쩔어', '쩐다', '쩔', '미쳤', '미침', '실화',
    '대단', '놀랍', '신기', '놀라',
    '레전드', '레전더리', '갓', 'god',
    '인정', '추천', '존경', '리스펙',
    '천재', '아름답', '환상', '최애',
    '역시', '믿고보는', '찐', '진짜',
    # 재미/유머 표현
    '꿀잼', '핵잼', '존잼', '개꿀', '킬링',
    '중독', '또봄', '반복', '계속', '루프',
    # 광고/콘텐츠 긍정
    '센스', '유머', '찰떡', '어울려', '어울림', '어울리',
    '소화', '매력', '아우라', '분위기', '비주얼',
    '작정', '본업', '프로', '장인', '퀄리티',
    '세련', '고급', '감각', '감성', '트렌디', '힙',
    # 영어
    'good', 'great', 'best', 'love', 'amazing', 'awesome',
    'beautiful', 'excellent', 'fantastic', 'perfect', 'nice',
    'wonderful', 'incredible', 'brilliant', 'cute', 'pretty',
    'wow', 'omg', 'fire', 'goat', 'legend', 'icon', 'queen', 'king',
}

NEGATIVE_WORDS = {
    # 명확한 부정만
    '싫어', '싫다', '싫음', '별로', '최악',
    '실망', '실망했', '실망스럽',
    '짜증', '짜증나', '짜증남',
    '화나', '화남', '열받',
    '답답', '불쾌', '불편',
    '슬프', '슬퍼', '우울',
    '지루', '지루해', '지루함',
    '노잼', '재미없', '재미가없',
    '못생', '못했', '못하',
    '쓰레기', '쓰렉', '망했', '망함', '폭망',
    '극혐', '혐오', '역겹',
    '비추', '비추천',
    '후회', '아깝', '돈아까',
    # 영어
    'bad', 'worst', 'hate', 'terrible', 'awful',
    'boring', 'disappointing', 'disappointed',
    'trash', 'garbage', 'sucks', 'cringe',
}

POSITIVE_EMOJIS = set('😀😃😄😁😆😅🤣😂😊😇🥰😍🤩😘👍👏🙌💪✨🌟⭐💖💗❤🔥💯🎉👑💎🏆😎🤗🥳')
NEGATIVE_EMOJIS = set('😢😭😤😠😡🤬💔👎🙄😒😞😔😟😣😖😫😩😱🤮🤢')

# =============================================================================
# 유틸리티 함수
# =============================================================================
def extract_video_id(url: str) -> str:
    """유튜브 URL에서 영상 ID 추출"""
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
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    return None

def format_date(date_str: str) -> str:
    """날짜 포맷팅 (YYYYMMDD → YYYY.MM.DD)"""
    if not date_str or len(date_str) != 8:
        return "정보 없음"
    return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"

def format_number(num) -> str:
    """숫자 포맷팅 (만/억 단위)"""
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

def analyze_sentiment(text: str) -> tuple:
    """
    댓글 감성 분석
    Returns: (sentiment, score) - sentiment는 'positive', 'negative', 'neutral' 중 하나
    """
    if not text:
        return 'neutral', 0.0
    
    text_lower = text.lower()
    score = 0.0
    
    # 1. 이모지 분석
    pos_emoji = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_emoji = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    if pos_emoji + neg_emoji > 0:
        score += (pos_emoji - neg_emoji) * 0.3
    
    # 2. 키워드 분석
    words = re.findall(r'[가-힣]+|[a-zA-Z]+', text_lower)
    pos_count = 0
    neg_count = 0
    
    for word in words:
        for pw in POSITIVE_WORDS:
            if pw in word or word in pw:
                pos_count += 1
                break
        for nw in NEGATIVE_WORDS:
            if nw in word or word in nw:
                neg_count += 1
                break
    
    if pos_count > 0:
        score += pos_count * 0.4
    if neg_count > 0:
        score -= neg_count * 0.5  # 부정은 가중치 더 높게
    
    # 3. 웃음 표현 (ㅋㅋ, ㅎㅎ) - 긍정 신호
    laugh = len(re.findall(r'ㅋ{2,}|ㅎ{2,}', text))
    if laugh > 0:
        score += laugh * 0.3
    
    # 4. 부정 패턴
    if re.search(r'ㅡㅡ+|;;+', text) and pos_count == 0:
        score -= 0.3
    
    # 판정
    if score >= 0.3:
        return 'positive', score
    elif score <= -0.3:
        return 'negative', score
    return 'neutral', score

def get_comment_period(comments: list) -> str:
    """댓글 작성 기간 추정 (최근 댓글 기준 추정)"""
    if not comments:
        return "정보 없음"
    # yt-dlp는 댓글 날짜를 제공하지 않으므로 추정
    count = len(comments)
    if count > 400:
        return "활발한 댓글 활동 (수백 개 이상)"
    elif count > 100:
        return "보통 수준의 댓글 활동"
    else:
        return "적은 댓글 활동"

def generate_insight(video_info: dict, pos_pct: float, neg_pct: float, 
                     pos_comments: list, neg_comments: list, keywords: list) -> str:
    """전체 분석 인사이트 생성"""
    insights = []
    
    # 1. 전반적 반응
    if pos_pct >= 70:
        insights.append(f"이 영상은 **매우 긍정적인 반응**을 얻고 있습니다 (긍정 {pos_pct:.0f}%). 시청자 만족도가 높아 추가 콘텐츠 제작이나 시리즈화를 고려해볼 만합니다.")
    elif pos_pct >= 50:
        insights.append(f"전반적으로 **호의적인 반응**입니다 (긍정 {pos_pct:.0f}%). 다만 중립/부정 의견도 있어 개선 포인트를 확인해볼 필요가 있습니다.")
    elif pos_pct >= 30:
        insights.append(f"**반응이 엇갈리고** 있습니다 (긍정 {pos_pct:.0f}%, 부정 {neg_pct:.0f}%). 부정 댓글의 구체적인 불만 사항을 파악하는 것이 중요합니다.")
    else:
        insights.append(f"**부정적 반응이 우세**합니다 (부정 {neg_pct:.0f}%). 시청자 피드백을 면밀히 분석하고 대응 전략이 필요합니다.")
    
    # 2. 부정 의견 경향
    if neg_pct > 20 and neg_comments:
        insights.append("부정 댓글에서 반복되는 패턴이 있다면 해당 이슈에 대한 해명이나 개선이 필요할 수 있습니다.")
    
    # 3. 키워드 기반
    if keywords:
        top_kw = keywords[0][0]
        insights.append(f"시청자들이 가장 많이 언급한 키워드는 **'{top_kw}'**입니다. 이 주제를 중심으로 후속 콘텐츠를 기획하면 관심을 유지할 수 있습니다.")
    
    # 4. 참여도
    view_count = video_info.get('view_count', 0)
    comment_count = video_info.get('total_comments', 0)
    if view_count > 0 and comment_count > 0:
        engagement = comment_count / view_count * 100
        if engagement > 1:
            insights.append("조회수 대비 댓글 참여율이 높아 시청자 몰입도가 좋습니다.")
    
    return " ".join(insights)

# =============================================================================
# 댓글 수집
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_video_data(url: str, max_comments: int):
    """유튜브 영상 정보 및 댓글 수집"""
    import yt_dlp
    
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'getcomments': True,
        'extractor_args': {
            'youtube': {
                'max_comments': [str(max_comments)],
                'comment_sort': ['top'],  # 인기순
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
# 키워드 추출
# =============================================================================
STOPWORDS = {'은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '도', '만', '로', '으로',
             '하고', '그리고', '그런데', '하지만', '그래서', '또', '더', '막', '좀', '이제', '진짜', '너무', '정말',
             '것', '거', '수', '때', '중', '년', '월', '일', '번', '분', '게', '데', '뭐', '왜',
             '나', '너', '우리', '저', '영상', '댓글', '유튜브', '채널', '구독', '좋아요',
             'the', 'a', 'an', 'is', 'are', 'to', 'of', 'in', 'for', 'on', 'with', 'this', 'that',
             'i', 'you', 'it', 'and', 'but', 'or', 'so', 'video', 'comment'}

def extract_keywords(texts: list, top_n: int = 10) -> list:
    """댓글에서 키워드 추출"""
    words = []
    for text in texts:
        if not text:
            continue
        # 전처리
        text = re.sub(r'http\S+', '', text.lower())
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        tokens = text.split()
        words.extend([t for t in tokens if t not in STOPWORDS and len(t) > 1])
    
    return Counter(words).most_common(top_n)

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 헤더
    st.markdown('''
    <div class="main-header">
        <h1>📊 유튜브 댓글 분석기</h1>
        <p>영상 URL을 입력하면 댓글을 분석합니다</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 입력
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed"
        )
        st.caption(f"⚠️ 댓글은 최대 **{MAX_COMMENTS}개**까지 분석합니다 (인기순 기준)")
        
        analyze_btn = st.button("🔍 분석 시작", use_container_width=True)
    
    # 분석 실행
    if analyze_btn and url:
        video_id = extract_video_id(url)
        
        if not video_id:
            st.error("❌ 올바른 YouTube URL을 입력해주세요.")
            return
        
        try:
            # 데이터 수집
            with st.spinner("댓글을 수집하고 있습니다... (최대 1분 소요)"):
                video_info, comments = fetch_video_data(url, MAX_COMMENTS)
            
            if not video_info:
                st.error("❌ 영상 정보를 가져올 수 없습니다.")
                return
            
            if not comments:
                st.warning("⚠️ 댓글이 없거나 댓글을 가져올 수 없습니다.")
                return
            
            # 분석
            with st.spinner("댓글을 분석하고 있습니다..."):
                # 감성 분석
                sentiments = [analyze_sentiment(c['text']) for c in comments]
                for i, (sent, score) in enumerate(sentiments):
                    comments[i]['sentiment'] = sent
                    comments[i]['score'] = score
                
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
            
            # ===== 결과 출력 =====
            st.markdown("---")
            
            # 1. 영상 정보
            st.markdown('<div class="section-title">📺 영상 정보</div>', unsafe_allow_html=True)
            
            total_comments = video_info.get('total_comments', 0)
            analyzed_count = len(comments)
            
            st.markdown(f'''
            <div class="info-box">
                <div class="info-row">
                    <span class="info-label">영상 제목</span>
                    <span class="info-value">{video_info.get("title", "")}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">채널명</span>
                    <span class="info-value">{video_info.get("channel", "")}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">게시일</span>
                    <span class="info-value">{video_info.get("upload_date", "")}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">조회수</span>
                    <span class="info-value">{format_number(video_info.get("view_count", 0))}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">댓글 현황</span>
                    <span class="info-value">전체 {format_number(total_comments)}개 중 상위 {analyzed_count}개 분석</span>
                </div>
                <div class="info-row">
                    <span class="info-label">댓글 활동</span>
                    <span class="info-value">{get_comment_period(comments)}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 2. 감성 분석 결과
            st.markdown('<div class="section-title">📊 감성 분석 결과</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:#2ecc71">{pos_pct:.1f}%</div>
                    <div class="metric-label">😊 긍정 ({pos_count}개)</div>
                </div>
                ''', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:#95a5a6">{neu_pct:.1f}%</div>
                    <div class="metric-label">😐 중립 ({neu_count}개)</div>
                </div>
                ''', unsafe_allow_html=True)
            with col3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:#e74c3c">{neg_pct:.1f}%</div>
                    <div class="metric-label">😞 부정 ({neg_count}개)</div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.caption("※ 분석 기준: 긍정/부정 키워드, 이모지, 웃음 표현(ㅋㅋ, ㅎㅎ) 등 종합 판단")
            
            # 3. 긍부정 댓글 경향성
            st.markdown('<div class="section-title">📈 댓글 경향성</div>', unsafe_allow_html=True)
            
            # 긍정 경향
            pos_df = df[df['sentiment'] == 'positive']
            if len(pos_df) > 0:
                pos_texts = ' '.join(pos_df['text'].tolist())
                pos_kw = extract_keywords([pos_texts], 5)
                pos_trend = ", ".join([k for k, _ in pos_kw]) if pos_kw else "특별한 패턴 없음"
                st.markdown(f"**😊 긍정 댓글 키워드**: {pos_trend}")
            
            # 부정 경향
            neg_df = df[df['sentiment'] == 'negative']
            if len(neg_df) > 0:
                neg_texts = ' '.join(neg_df['text'].tolist())
                neg_kw = extract_keywords([neg_texts], 5)
                neg_trend = ", ".join([k for k, _ in neg_kw]) if neg_kw else "특별한 패턴 없음"
                st.markdown(f"**😞 부정 댓글 키워드**: {neg_trend}")
            else:
                st.markdown("**😞 부정 댓글**: 거의 없음")
            
            # 4. 긍부정 댓글 예시
            st.markdown('<div class="section-title">💬 대표 댓글</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👍 긍정 댓글 예시**")
                pos_samples = pos_df.nlargest(3, 'likes') if len(pos_df) > 0 else []
                if len(pos_samples) > 0:
                    for _, row in pos_samples.iterrows():
                        text = row['text'][:120] + ('...' if len(row['text']) > 120 else '')
                        st.markdown(f'''
                        <div class="comment-box positive">
                            <div class="comment-text">"{text}"</div>
                            <div class="comment-meta">👍 {int(row["likes"]):,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info("긍정 댓글이 없습니다.")
            
            with col2:
                st.markdown("**👎 부정 댓글 예시**")
                neg_samples = neg_df.nlargest(3, 'likes') if len(neg_df) > 0 else []
                if len(neg_samples) > 0:
                    for _, row in neg_samples.iterrows():
                        text = row['text'][:120] + ('...' if len(row['text']) > 120 else '')
                        st.markdown(f'''
                        <div class="comment-box negative">
                            <div class="comment-text">"{text}"</div>
                            <div class="comment-meta">👍 {int(row["likes"]):,}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.success("🎉 부정 댓글이 거의 없습니다!")
            
            # 5. 베스트 댓글 TOP 5
            st.markdown('<div class="section-title">🏆 베스트 댓글 TOP 5</div>', unsafe_allow_html=True)
            
            top_comments = df.nlargest(5, 'likes')
            for i, (_, row) in enumerate(top_comments.iterrows(), 1):
                text = row['text'][:150] + ('...' if len(row['text']) > 150 else '')
                st.markdown(f'''
                <div class="comment-box best">
                    <div class="comment-text"><strong>#{i}</strong> "{text}"</div>
                    <div class="comment-meta">👍 {int(row["likes"]):,}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 6. 종합 인사이트
            st.markdown('<div class="section-title">💡 종합 인사이트</div>', unsafe_allow_html=True)
            
            insight = generate_insight(
                video_info, pos_pct, neg_pct,
                pos_df.to_dict('records') if len(pos_df) > 0 else [],
                neg_df.to_dict('records') if len(neg_df) > 0 else [],
                keywords
            )
            
            st.markdown(f'''
            <div class="insight-box">
                <div class="insight-text">{insight}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 푸터
            st.markdown("---")
            st.caption("유튜브 댓글 분석기 v1.0")
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            st.info("💡 유효한 YouTube URL인지 확인해주세요. 비공개 영상이나 댓글이 비활성화된 영상은 분석할 수 없습니다.")

if __name__ == "__main__":
    main()
