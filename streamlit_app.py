#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 인사이트 분석기 - Streamlit 버전
Streamlit Cloud 무료 배포용
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from typing import List, Dict, Tuple, Optional

# =============================================================================
# 페이지 설정
# =============================================================================

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# =============================================================================
# 설정
# =============================================================================

CONFIG = {
    "max_comments": 2000,
    "top_keywords_count": 30,
    "num_topics": 5,
    "min_comment_length": 2,
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
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
    'it', 'its', 'they', 'them', 'their', 'this', 'that', 'these', 'those',
    'and', 'but', 'if', 'or', 'so', 'than', 'too', 'very', 'just',
    'video', 'comment', 'youtube', 'channel', 'subscribe', 'watch',
])


# =============================================================================
# 유틸리티
# =============================================================================

def extract_video_id(url: str) -> Optional[str]:
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


def preprocess_for_analysis(text: str) -> str:
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


def format_upload_date(date_str: str) -> str:
    if not date_str or len(date_str) != 8:
        return "날짜 정보 없음"
    try:
        return f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
    except:
        return date_str


# =============================================================================
# 댓글 수집기
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def collect_comments(url: str, max_comments: int) -> Tuple[Dict, List[Dict]]:
    """댓글 수집 (캐싱 적용)"""
    import yt_dlp
    
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
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        upload_date = info.get('upload_date', '')
        
        video_info = {
            'video_id': info.get('id', ''),
            'title': info.get('title', 'N/A'),
            'channel': info.get('channel', info.get('uploader', 'N/A')),
            'thumbnail': info.get('thumbnail', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'comment_count': info.get('comment_count', 0),
            'upload_date': format_upload_date(upload_date),
        }
        
        raw_comments = info.get('comments', [])
        comments = []
        for i, c in enumerate(raw_comments):
            if i >= max_comments:
                break
            comments.append({
                'comment_id': c.get('id', str(i)),
                'text': c.get('text', ''),
                'like_count': c.get('like_count', 0),
                'author': c.get('author', ''),
            })
        
        return video_info, comments


# =============================================================================
# 감성 분석기
# =============================================================================

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = {
            '좋다', '좋아', '좋네', '좋은', '좋았', '좋음', '좋고', '좋죠', '좋아요', '좋습니다',
            '최고', '최곱니다', '최고다', '최고야', '최고예요', '최고임', '최고에요',
            '대박', '대박이다', '대박이야', '대박이네',
            '멋지다', '멋져', '멋있다', '멋있어', '멋짐', '멋진',
            '예쁘다', '예뻐', '예쁨', '예쁜', '이쁘다', '이뻐', '이쁨',
            '사랑', '사랑해', '사랑해요', '사랑합니다', '사랑스러', '사랑스럽',
            '감사', '감사해요', '감사합니다', '고마워', '고맙습니다', '고마워요',
            '행복', '행복해', '행복하다', '기쁘다', '기뻐', '즐겁다', '즐거워',
            '기대', '기대된다', '기대돼', '기대됩니다', '기대해',
            '응원', '응원해', '응원합니다', '응원해요', '화이팅', '파이팅', '힘내',
            '축하', '축하해', '축하합니다', '축하드려요',
            '훌륭', '훌륭해', '훌륭하다', '완벽', '완벽해', '완벽하다',
            '감동', '감동이다', '감동이야', '감동받았', '감동적',
            '재밌', '재밌다', '재밌어', '재밌네', '재미있', '재미있다', '재미있어',
            '웃기다', '웃겨', '웃김', '웃긴',
            '힐링', '힐링된다', '힐링이다',
            '귀엽', '귀여워', '귀엽다', '귀여운', '깜찍',
            '잘생', '잘생겼', '잘생김', '존잘', '핸섬',
            '존예', '개예', '겁나예뻐', '너무예뻐',
            '짱', '짱이다', '짱이야', '쩔어', '쩐다', '쩔었', '쩔어요',
            '미쳤', '미쳤다', '미쳤어', '미침', '미친',
            '죽는다', '죽겠다', '죽을것같', '죽음',
            '대단', '대단해', '대단하다', '대단하네',
            '놀랍', '놀라워', '놀랍다', '신기', '신기해', '신기하다',
            '레전드', '레전더리', 'legend', 'goat',
            '인정', '인정합니다', '인정이요',
            '추천', '추천해', '추천합니다',
            '갓', '갓벽', 'god',
            '존경', '존경해', '존경합니다', '리스펙', 'respect',
            '멋있', '간지', '간지나', '간지남', '폼', '폼나',
            '천재', '천재다', '천재적',
            '아름답', '아름다워', '아름다운', '황홀', '환상적',
            '역시', '역시나', '믿고보는', '믿보',
            '찐', '찐이다', '찐이야', '리얼', '진짜다',
            '꿀잼', '핵잼', '존잼', '개꿀', '개이득',
            '소름', '소름돋', '전율', '감탄',
            '눈물', '눈물나', '울컥', '찡', '찡하다',
            '힘이된다', '위로가된다', '공감', '공감돼',
            'good', 'great', 'best', 'love', 'like', 'amazing', 'awesome', 'wonderful',
            'beautiful', 'excellent', 'fantastic', 'nice', 'perfect', 'happy', 'cool',
            'incredible', 'brilliant', 'outstanding', 'superb', 'magnificent', 'lovely',
            'talented', 'genius', 'wow', 'omg', 'fire', 'lit', 'sick', 'dope',
            'queen', 'king', 'icon', 'iconic', 'slay', 'slayed', 'serve', 'ate',
            'proud', 'blessed', 'grateful', 'touched', 'moved',
            'support', 'stan', 'bias', 'fave', 'favorite',
        }
        
        self.negative_words = {
            '싫다', '싫어', '싫음', '싫네',
            '별로', '별로다', '별로야', '별루',
            '최악', '최악이다', '최악이야',
            '실망', '실망이다', '실망이야', '실망했', '실망스럽',
            '짜증', '짜증나', '짜증난다', '짜증나네',
            '화나', '화난다', '화남', '분노', '열받',
            '답답', '답답하다', '답답해',
            '불쾌', '불쾌하다', '불쾌해',
            '슬프', '슬퍼', '슬프다', '슬픔', '우울', '우울하다',
            '안타깝', '안타까워', '아쉽', '아쉽다', '아쉬워',
            '걱정', '걱정된다', '걱정돼', '불안', '불안하다',
            '힘들', '힘들다', '힘들어', '지침', '지쳤', '피곤',
            '나쁘', '나빠', '나쁜', '못하', '못함', '못해',
            '후회', '후회된다', '후회돼',
            '혐오', '역겹', '역겨워', '구역질',
            '지루', '지루하다', '지루해', '노잼', '재미없',
            '망했', '망함', '망작', '폭망', '쫄딱망',
            '쓰레기', '쓰렉', '별점테러',
            '거부감', '불편', '불편하다',
            '비추', '비추천', '비추다',
            'bad', 'worst', 'hate', 'dislike', 'terrible', 'awful', 'horrible',
            'sad', 'angry', 'disappointed', 'disappointing', 'boring', 'annoying',
            'frustrated', 'worried', 'fail', 'failed', 'failure', 'wrong',
            'disgusting', 'pathetic', 'waste', 'garbage', 'trash', 'cringe',
            'overrated', 'underwhelming', 'meh',
        }
        
        self.positive_emojis = {
            '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😊', '😇',
            '🥰', '😍', '🤩', '😘', '😗', '😚', '😙', '🥲',
            '👍', '👏', '🙌', '💪', '✨', '🌟', '⭐', '💖', '💗', '💓', '💕',
            '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '💝', '💘', '♥️', '❤',
            '🔥', '💯', '🎉', '🎊', '👑', '💎', '🏆', '🥇',
            '😎', '🤗', '🥳', '😋', '😜', '😝', '🤭', '🫶', '🫰',
            '👀', '💀',
        }
        
        self.negative_emojis = {
            '😢', '😭', '😤', '😠', '😡', '🤬', '😈', '👿',
            '💔', '👎', '🙄', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️',
            '😣', '😖', '😫', '😩', '🥺', '😰', '😨', '😱', '🤮', '🤢',
        }
        
        self.positive_patterns = [
            r'ㅋ{2,}', r'ㅎ{2,}', r'！{2,}|!{2,}', r'♡+|♥+',
            r'최고+', r'대박+', r'미쳤+', r'헐+', r'와+[ㅏ-ㅣ]*', r'우+와+',
        ]
        
        self.negative_patterns = [
            r'ㅡㅡ+', r';;+', r'에휴+|에혀+', r'한숨',
        ]
    
    def analyze(self, text: str) -> Tuple[str, float]:
        if not text or not isinstance(text, str):
            return 'neutral', 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # 이모지
        pos_emoji = sum(1 for e in self.positive_emojis if e in text)
        neg_emoji = sum(1 for e in self.negative_emojis if e in text)
        if pos_emoji + neg_emoji > 0:
            score += (pos_emoji - neg_emoji) / (pos_emoji + neg_emoji + 1) * 1.5
        
        # 단어
        words = set(re.findall(r'[가-힣]+|[a-z]+', text_lower))
        pos_count = sum(1 for w in words if any(pw in w or w in pw for pw in self.positive_words))
        neg_count = sum(1 for w in words if any(nw in w or w in nw for nw in self.negative_words))
        if pos_count + neg_count > 0:
            score += (pos_count - neg_count) / (pos_count + neg_count + 0.5)
        
        # 패턴
        pos_pat = sum(1 for p in self.positive_patterns if re.search(p, text))
        neg_pat = sum(1 for p in self.negative_patterns if re.search(p, text))
        score += (pos_pat - neg_pat) * 0.24
        
        # 느낌표
        exclaim = text.count('!') + text.count('！')
        if exclaim >= 2:
            score += 0.15
        
        if score > 0.1:
            return 'positive', min(score, 1.0)
        elif score < -0.1:
            return 'negative', max(score, -1.0)
        return 'neutral', score
    
    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        results = [self.analyze(text) for text in df['text'].fillna('')]
        df['sentiment_label'] = [r[0] for r in results]
        df['sentiment_score'] = [r[1] for r in results]
        return df


# =============================================================================
# 키워드 분석
# =============================================================================

def extract_keywords(texts: List[str], top_n: int = 20) -> List[Tuple[str, float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    processed = [preprocess_for_analysis(t) for t in texts if preprocess_for_analysis(t)]
    if len(processed) < 10:
        return []
    
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2000, min_df=2, max_df=0.85)
        tfidf = vectorizer.fit_transform(processed)
        features = vectorizer.get_feature_names_out()
        mean_tfidf = np.asarray(tfidf.mean(axis=0)).flatten()
        top_idx = mean_tfidf.argsort()[::-1][:top_n]
        return [(features[i], mean_tfidf[i]) for i in top_idx]
    except:
        return []


# =============================================================================
# 토픽 모델링
# =============================================================================

def perform_topic_modeling(texts: List[str], num_topics: int = 5) -> Dict:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    
    processed = [preprocess_for_analysis(t) for t in texts if preprocess_for_analysis(t)]
    if len(processed) < num_topics * 10:
        return {}
    
    try:
        vectorizer = CountVectorizer(ngram_range=(1, 2), max_features=1500, min_df=3, max_df=0.8)
        doc_term = vectorizer.fit_transform(processed)
        lda = LatentDirichletAllocation(n_components=num_topics, max_iter=10, random_state=42)
        doc_topics = lda.fit_transform(doc_term)
        features = vectorizer.get_feature_names_out()
        
        topics = {}
        for idx, topic in enumerate(lda.components_):
            top_idx = topic.argsort()[:-11:-1]
            topics[idx] = {'keywords': [features[i] for i in top_idx]}
        
        return {'topics': topics, 'assignments': doc_topics.argmax(axis=1)}
    except:
        return {}


def get_topic_summaries(df: pd.DataFrame, topic_result: Dict, num_topics: int = 5) -> List[Dict]:
    if not topic_result:
        return []
    
    assignments = topic_result['assignments']
    valid_mask = df['text'].apply(lambda x: len(preprocess_for_analysis(str(x))) > 0)
    valid_df = df[valid_mask].reset_index(drop=True)
    
    min_len = min(len(valid_df), len(assignments))
    valid_df = valid_df.iloc[:min_len].copy()
    valid_df['topic'] = assignments[:min_len]
    
    summaries = []
    for idx in range(num_topics):
        topic_df = valid_df[valid_df['topic'] == idx]
        if len(topic_df) == 0:
            continue
        
        sent_dist = topic_df['sentiment_label'].value_counts(normalize=True)
        sentiment = {
            'positive': sent_dist.get('positive', 0) * 100,
            'neutral': sent_dist.get('neutral', 0) * 100,
            'negative': sent_dist.get('negative', 0) * 100,
        }
        
        summaries.append({
            'keywords': topic_result['topics'][idx]['keywords'][:6],
            'count': len(topic_df),
            'pct': len(topic_df) / len(valid_df) * 100,
            'sentiment': sentiment,
        })
    
    summaries.sort(key=lambda x: x['count'], reverse=True)
    return summaries


# =============================================================================
# 인사이트 생성
# =============================================================================

def generate_insights(pos_pct: float, neg_pct: float, top_pos_ratio: float, 
                      keywords: List, topic_summaries: List) -> List[Dict]:
    insights = []
    
    if pos_pct > 60:
        insights.append({
            'title': '🔥 강력한 팬덤 기반의 긍정적 바이럴 잠재력',
            'desc': f'전체 댓글의 {pos_pct:.0f}%가 긍정적 반응입니다. 이는 "자발적 홍보 의지"를 가진 팬층이 형성되어 있음을 의미합니다. 좋아요 상위 댓글의 {top_pos_ratio:.0f}%가 긍정인 점은 여론 주도층이 우호적이라는 신호입니다.',
            'action': 'UGC 캠페인, 팬 참여형 챌린지 등 "팬이 홍보대사가 되는" 전략 추천'
        })
    elif pos_pct > 40:
        insights.append({
            'title': '👀 호의적이나 "열성 팬"으로 전환되지 않은 층 존재',
            'desc': f'긍정 비율 {pos_pct:.0f}%는 괜찮은 수치이나, "좋아하지만 굳이 찾아보진 않는" 가벼운 관심층일 가능성이 높습니다.',
            'action': '정기적 터치포인트(비하인드, 팬서비스 콘텐츠)로 관계 깊이를 더해야 함'
        })
    
    if neg_pct > 20:
        insights.append({
            'title': '⚠️ 부정 여론의 "핵심 불만" 파악 필요',
            'desc': f'부정 반응이 {neg_pct:.0f}%로 무시할 수 없습니다. 콘텐츠 퀄리티 문제인지, 기대와의 괴리인지 파악이 필요합니다.',
            'action': '부정 댓글 키워드 분석 후, 해명/개선이 필요한 영역 식별'
        })
    
    if topic_summaries:
        t = topic_summaries[0]
        insights.append({
            'title': f'💬 "{t["keywords"][0]}" - 시청자가 가장 말하고 싶어하는 주제',
            'desc': f'전체 댓글의 {t["pct"]:.0f}%가 이 주제를 언급합니다. 사람들은 관심 없는 것에 댓글을 달지 않습니다.',
            'action': f'"{t["keywords"][0]}" 주제로 후속 콘텐츠 기획 시 높은 engagement 예상'
        })
    
    if keywords:
        kws = [k for k, _ in keywords[:5]]
        insights.append({
            'title': '📝 시청자 언어로 말하라',
            'desc': f'가장 많이 언급된 키워드: "{", ".join(kws)}". 마케팅 메시지, 썸네일, 제목에 활용하면 공감을 이끌어낼 수 있습니다.',
            'action': f'다음 콘텐츠에 "{kws[0]}", "{kws[1] if len(kws) > 1 else ""}" 전략적 활용'
        })
    
    return insights


# =============================================================================
# 메인 앱
# =============================================================================

def main():
    # CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
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
        margin-bottom: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .insight-title {
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .insight-action {
        font-size: 0.9rem;
        color: #2d5a87;
        font-style: italic;
        margin-top: 0.5rem;
    }
    .topic-tag {
        display: inline-block;
        background: #d4e4f1;
        color: #1e3a5f;
        padding: 0.2rem 0.8rem;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    .comment-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #7ba3cc;
    }
    .comment-box.positive { border-color: #2d5a87; }
    .comment-box.negative { border-color: #8b4557; }
    </style>
    """, unsafe_allow_html=True)
    
    # 헤더
    st.markdown('<p class="main-header">📊 유튜브 댓글 분석기</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">영상 URL을 입력하면 댓글 인사이트 리포트를 생성합니다</p>', unsafe_allow_html=True)
    
    # URL 입력
    col1, col2 = st.columns([4, 1])
    with col1:
        url = st.text_input("유튜브 URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
    with col2:
        analyze_btn = st.button("🔍 분석", type="primary", use_container_width=True)
    
    if analyze_btn and url:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("❌ 유효하지 않은 YouTube URL입니다.")
            return
        
        try:
            # 진행 상태
            progress = st.progress(0)
            status = st.empty()
            
            status.text("📥 댓글 수집 중... (1~2분 소요)")
            progress.progress(10)
            
            video_info, comments = collect_comments(url, CONFIG["max_comments"])
            
            if not comments:
                st.error("❌ 댓글을 가져올 수 없습니다.")
                return
            
            progress.progress(40)
            status.text("🔍 감성 분석 중...")
            
            df = pd.DataFrame(comments)
            analyzer = SentimentAnalyzer()
            df = analyzer.analyze_dataframe(df)
            
            progress.progress(60)
            status.text("📊 키워드 추출 중...")
            
            texts = df[df['text'].str.len() >= CONFIG["min_comment_length"]]['text'].tolist()
            keywords = extract_keywords(texts, CONFIG["top_keywords_count"])
            
            progress.progress(80)
            status.text("🏷️ 토픽 분석 중...")
            
            topic_result = perform_topic_modeling(texts, CONFIG["num_topics"])
            topic_summaries = get_topic_summaries(df, topic_result, CONFIG["num_topics"])
            
            progress.progress(100)
            status.empty()
            progress.empty()
            
            # =====================
            # 결과 표시
            # =====================
            
            st.divider()
            
            # 영상 정보
            col1, col2 = st.columns([1, 3])
            with col1:
                if video_info.get('thumbnail'):
                    st.image(video_info['thumbnail'], use_container_width=True)
            with col2:
                st.markdown(f"### {video_info.get('title', 'N/A')}")
                st.markdown(f"**{video_info.get('channel', '')}** · 업로드: {video_info.get('upload_date', 'N/A')}")
            
            st.divider()
            
            # 주요 지표
            total = len(df)
            pos_count = (df['sentiment_label'] == 'positive').sum()
            neu_count = (df['sentiment_label'] == 'neutral').sum()
            neg_count = (df['sentiment_label'] == 'negative').sum()
            pos_pct = pos_count / total * 100 if total > 0 else 0
            neg_pct = neg_count / total * 100 if total > 0 else 0
            
            top_liked = df.nlargest(20, 'like_count')
            top_pos_ratio = (top_liked['sentiment_label'] == 'positive').sum() / len(top_liked) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("분석 댓글", f"{total:,}개")
            col2.metric("긍정률", f"{pos_pct:.1f}%")
            col3.metric("부정률", f"{neg_pct:.1f}%")
            col4.metric("조회수", f"{video_info.get('view_count', 0):,}")
            
            st.divider()
            
            # 차트
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 감성 분포")
                import plotly.express as px
                fig = px.pie(
                    values=[pos_count, neu_count, neg_count],
                    names=['긍정', '중립', '부정'],
                    color_discrete_sequence=['#2d5a87', '#a8c5de', '#8b4557'],
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 핵심 키워드")
                if keywords:
                    kw_df = pd.DataFrame(keywords[:10], columns=['키워드', '점수'])
                    kw_df['점수'] = kw_df['점수'] * 1000
                    fig = px.bar(
                        kw_df, y='키워드', x='점수', orientation='h',
                        color_discrete_sequence=['#2d5a87']
                    )
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("키워드 데이터가 충분하지 않습니다.")
            
            st.divider()
            
            # 인사이트
            st.markdown("### 💡 핵심 인사이트")
            insights = generate_insights(pos_pct, neg_pct, top_pos_ratio, keywords, topic_summaries)
            for ins in insights:
                st.markdown(f"""
                <div class="insight-box">
                    <div class="insight-title">{ins['title']}</div>
                    <div>{ins['desc']}</div>
                    <div class="insight-action">→ {ins['action']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # 토픽 & 댓글
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🏷️ 토픽별 분석")
                for i, t in enumerate(topic_summaries[:5], 1):
                    with st.expander(f"토픽 {i}: {', '.join(t['keywords'][:3])} ({t['count']:,}개, {t['pct']:.0f}%)"):
                        tags = ''.join([f'<span class="topic-tag">{k}</span>' for k in t['keywords'][:6]])
                        st.markdown(tags, unsafe_allow_html=True)
                        st.progress(t['sentiment']['positive'] / 100)
                        st.caption(f"긍정 {t['sentiment']['positive']:.0f}% / 중립 {t['sentiment']['neutral']:.0f}% / 부정 {t['sentiment']['negative']:.0f}%")
            
            with col2:
                st.markdown("#### 💬 주요 댓글")
                
                st.markdown("**긍정 반응**")
                for _, row in df[df['sentiment_label'] == 'positive'].nlargest(3, 'like_count').iterrows():
                    text = str(row['text'])[:100] + ('...' if len(str(row['text'])) > 100 else '')
                    st.markdown(f"""
                    <div class="comment-box positive">
                        "{text}"<br>
                        <small>👍 {row['like_count']:,}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("**부정/우려**")
                for _, row in df[df['sentiment_label'] == 'negative'].nlargest(3, 'like_count').iterrows():
                    text = str(row['text'])[:100] + ('...' if len(str(row['text'])) > 100 else '')
                    st.markdown(f"""
                    <div class="comment-box negative">
                        "{text}"<br>
                        <small>👍 {row['like_count']:,}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # 액션 아이템
            st.markdown("### ✅ 액션 아이템")
            actions = []
            if pos_pct > 50:
                actions.append("팬 참여형 콘텐츠(Q&A, 투표, 챌린지) 기획으로 engagement 극대화")
            if neg_pct > 20:
                actions.append("부정 댓글 패턴 분석 후 FAQ 또는 공지 형태의 선제적 커뮤니케이션")
            if topic_summaries:
                actions.append(f'"{topic_summaries[0]["keywords"][0]}" 주제 확장 콘텐츠로 시청자 관심 지속 유도')
            if keywords:
                actions.append(f'"{keywords[0][0]}" 키워드 활용한 썸네일/제목 A/B 테스트')
            actions.append("열성 팬(반복 댓글러) 식별 후 앰배서더/VIP 프로그램 타겟팅")
            
            for i, action in enumerate(actions, 1):
                st.markdown(f"**{i}.** {action}")
            
            st.divider()
            st.caption("YouTube Comment Insight Report · Auto-generated")
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()