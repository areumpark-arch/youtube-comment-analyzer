#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유튜브 댓글 인사이트 분석기 v7.0
================================
PDF 다운로드 + 마케터 키워드 분석
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
import io
import base64
from typing import List, Tuple, Optional
from collections import Counter
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
# 세션 상태 초기화
# =============================================================================
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .block-container { padding: 2rem 3rem !important; max-width: 1100px !important; }
    
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
    .video-info-label {
        color: #64748b;
        font-size: 0.85rem;
        min-width: 100px;
        font-weight: 500;
    }
    .video-info-value {
        color: #1e293b;
        font-size: 0.9rem;
        flex: 1;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a5f;
        margin: 2rem 0 1rem 0;
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
    
    .keyword-analysis {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-top: 1rem;
    }
    .keyword-analysis-title {
        font-weight: 600;
        color: #1e3a5f;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .keyword-analysis-text {
        color: #475569;
        font-size: 0.85rem;
        line-height: 1.7;
    }
    
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
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border-radius: 8px;
    }
    .stDownloadButton > button:hover {
        background: #1e3a5f;
        color: white;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        padding: 0.7rem 1rem;
    }
    
    [data-testid="stMetricValue"] { font-size: 1.6rem; color: #1e3a5f; }
    [data-testid="stMetricLabel"] { color: #64748b; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 설정
# =============================================================================
CONFIG = {"max_comments": 800, "top_keywords_count": 12}

STOPWORDS = set(['은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '도', '만', '로', '으로',
    '하고', '그리고', '그런데', '하지만', '그래서', '그러나', '또한', '및', '등',
    '나', '너', '우리', '저', '이것', '저것', '그것', '여기', '저기', '거기',
    '하다', '되다', '있다', '없다', '같다', '보다', '알다', '싶다', '주다',
    '하는', '하면', '해서', '했다', '한다', '할', '함', '되는', '되면', '됐다', '된다',
    '있는', '있으면', '있고', '있어서', '있었다', '있을', '있음',
    '것', '거', '수', '때', '중', '내', '년', '월', '일', '번', '분',
    '영상', '댓글', '동영상', '유튜브', '채널', '구독', '좋아요', '시청', '진짜', '너무', '정말',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'to', 'of', 'in', 'for', 'on', 'with',
    'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'and', 'but', 'or',
    'video', 'comment', 'youtube', 'channel', 'subscribe'])

POSITIVE_WORDS = {'좋다', '좋아', '좋네', '좋은', '좋았', '좋음', '좋아요', '좋습니다', '최고', '최고다', '최고야', '최고예요', '최고임',
    '대박', '대박이다', '멋지다', '멋져', '멋있다', '멋있어', '멋짐', '예쁘다', '예뻐', '예쁨', '이쁘다', '이뻐',
    '사랑', '사랑해', '사랑해요', '사랑합니다', '감사', '감사해요', '감사합니다', '고마워', '고맙습니다',
    '행복', '행복해', '기쁘다', '즐겁다', '기대', '기대된다', '기대돼', '응원', '응원해', '화이팅', '파이팅', '힘내',
    '훌륭', '완벽', '감동', '설렘', '설레', '재밌', '재밌다', '재미있', '웃기다', '웃겨', '힐링', '귀엽', '귀여워',
    '잘생', '잘생겼', '존잘', '존예', '짱', '쩔어', '쩐다', '미쳤', '미쳤다', '대단', '놀랍', '신기', '레전드',
    '인정', '추천', '갓', '존경', '천재', '아름답', '환상적', '역시', '믿고보는', '찐', '꿀잼', '핵잼', '존잼', '소름', '감탄', '공감',
    'good', 'great', 'best', 'love', 'like', 'amazing', 'awesome', 'beautiful', 'excellent', 'fantastic', 'perfect', 'happy',
    'incredible', 'brilliant', 'wow', 'omg', 'fire', 'goat', 'queen', 'king', 'icon', 'slay', 'legend'}

NEGATIVE_WORDS = {'싫다', '싫어', '별로', '최악', '실망', '짜증', '짜증나', '화나', '답답', '불쾌', '슬프', '우울',
    '아쉽', '걱정', '불안', '힘들', '피곤', '나쁘', '못하', '후회', '혐오', '역겹', '지루', '노잼', '재미없', '망했', '망함', '쓰레기', '불편', '비추',
    'bad', 'worst', 'hate', 'terrible', 'awful', 'sad', 'angry', 'disappointed', 'boring', 'fail', 'trash', 'cringe'}

POSITIVE_EMOJIS = set('😀😃😄😁😆😅🤣😂😊😇🥰😍🤩😘👍👏🙌💪✨🌟⭐💖💗❤🧡💛💚💙💜💝🔥💯🎉👑💎🏆😎🤗🥳❤️')
NEGATIVE_EMOJIS = set('😢😭😤😠😡🤬💔👎🙄😒😞😔😟🙁😣😖😫😩😱🤮🤢')

# =============================================================================
# 유틸리티
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
# 댓글 수집
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def collect_comments(url, max_comments):
    import yt_dlp
    opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'getcomments': True,
            'extractor_args': {'youtube': {'max_comments': [str(max_comments)], 'comment_sort': ['top']}}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info: return None, []
        video_info = {
            'title': info.get('title', '제목 없음'),
            'channel': info.get('channel', info.get('uploader', '')),
            'thumbnail': info.get('thumbnail', ''),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'upload_date': format_date(info.get('upload_date', '')),
            'url': url,
        }
        raw = info.get('comments') or []
        comments = [{'text': c.get('text', ''), 'like_count': c.get('like_count', 0) or 0} for c in raw[:max_comments] if c]
        return video_info, comments

# =============================================================================
# 감성 분석
# =============================================================================
def analyze_sentiment(text):
    if not text: return 'neutral', 0.0
    text_lower = text.lower()
    score = 0.0
    
    pos_e = sum(1 for e in POSITIVE_EMOJIS if e in text)
    neg_e = sum(1 for e in NEGATIVE_EMOJIS if e in text)
    if pos_e + neg_e > 0: score += (pos_e - neg_e) / (pos_e + neg_e + 1) * 1.5
    
    words = set(re.findall(r'[가-힣]+|[a-z]+', text_lower))
    pos_w = sum(1 for w in words if any(pw in w or w in pw for pw in POSITIVE_WORDS))
    neg_w = sum(1 for w in words if any(nw in w or w in nw for nw in NEGATIVE_WORDS))
    if pos_w + neg_w > 0: score += (pos_w - neg_w) / (pos_w + neg_w + 0.5)
    
    if re.search(r'ㅋ{2,}|ㅎ{2,}', text): score += 0.3
    if re.search(r'ㅡㅡ|;;', text): score -= 0.3
    if text.count('!') >= 2: score += 0.2
    
    if score > 0.1: return 'positive', min(score, 1.0)
    elif score < -0.1: return 'negative', max(score, -1.0)
    return 'neutral', score

# =============================================================================
# 키워드 + 마케터 분석
# =============================================================================
def extract_keywords(texts, top_n=12):
    words = []
    for t in texts:
        if t: words.extend(preprocess(str(t)).split())
    return Counter(words).most_common(top_n) if words else []

def generate_keyword_marketing_analysis(keywords, pos_pct, neg_pct, total):
    """10년차 SNS 마케터 관점의 키워드 분석"""
    if not keywords:
        return ""
    
    top_kws = [k for k, _ in keywords[:5]]
    kw_str = ', '.join(top_kws)
    top1 = keywords[0][0] if keywords else ""
    top1_count = keywords[0][1] if keywords else 0
    
    analysis = []
    
    # 1. 키워드 집중도 분석
    if top1_count > total * 0.1:
        analysis.append(f"▸ **키워드 집중도 높음**: '{top1}'이(가) 전체 댓글의 {top1_count/total*100:.1f}%에서 언급됩니다. "
                       f"이는 시청자들의 '핵심 관심사'가 명확하다는 의미입니다. 콘텐츠 포지셔닝이 잘 되어 있거나, "
                       f"특정 요소가 강렬한 인상을 남겼습니다.")
    else:
        analysis.append(f"▸ **키워드 분산형**: 특정 키워드에 집중되지 않고 다양한 반응이 나옵니다. "
                       f"시청자마다 다른 포인트에 반응하고 있어, 콘텐츠의 '핵심 메시지'를 더 명확히 할 필요가 있습니다.")
    
    # 2. 감정 vs 내용 키워드 비율
    emotion_words = {'사랑', '감동', '눈물', '소름', '설레', '행복', '슬프', '화나', '짜증', 'love', 'happy', 'sad', 'angry'}
    emotion_kws = [k for k, _ in keywords if any(e in k for e in emotion_words)]
    
    if len(emotion_kws) >= 2:
        analysis.append(f"▸ **감정 반응 활발**: 감정 관련 키워드({', '.join(emotion_kws[:3])})가 다수 등장합니다. "
                       f"시청자들이 '정서적으로 몰입'하고 있다는 신호입니다. 감정을 자극하는 콘텐츠는 공유율이 높습니다.")
    
    # 3. 콘텐츠 방향성 제안
    analysis.append(f"▸ **콘텐츠 방향성**: 시청자들이 '{top1}'에 강하게 반응하고 있습니다. "
                   f"다음 콘텐츠에서 '{top1}'를 메인 테마로 확장하거나, "
                   f"'{top1} + {top_kws[1] if len(top_kws) > 1 else '관련주제'}'를 결합한 기획을 추천합니다.")
    
    # 4. 광고/협찬 키워드 체크
    ad_words = {'광고', '협찬', 'ad', 'sponsored', '돈', '홍보'}
    ad_found = [k for k, _ in keywords if any(a in k for a in ad_words)]
    if ad_found:
        analysis.append(f"▸ **주의 필요**: '{', '.join(ad_found)}' 키워드가 감지되었습니다. "
                       f"시청자들이 상업적 요소에 민감하게 반응하고 있을 수 있습니다. 투명한 소통 권장.")
    
    # 5. 해시태그 추천
    hashtags = [f"#{k.replace(' ', '')}" for k, _ in keywords[:5]]
    analysis.append(f"▸ **추천 해시태그**: {' '.join(hashtags)}")
    
    return '\n\n'.join(analysis)

# =============================================================================
# 차트
# =============================================================================
def create_donut_chart(pos, neu, neg):
    colors = ['#1e3a5f', '#5a7fa8', '#a8c5de']
    fig = go.Figure(data=[go.Pie(
        values=[pos, neu, neg], labels=['긍정', '중립', '부정'], hole=0.55,
        marker=dict(colors=colors), textinfo='percent', textfont=dict(size=14, color='white'),
        hovertemplate='%{label}: %{value}개<br>%{percent}<extra></extra>', sort=False
    )])
    fig.update_layout(
        showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5, font=dict(size=12)),
        margin=dict(t=20, b=40, l=20, r=20), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )
    total = pos + neu + neg
    fig.add_annotation(text=f"<b>{total:,}</b><br><span style='font-size:11px;color:#64748b'>댓글</span>",
                      x=0.5, y=0.5, font=dict(size=18, color='#1e3a5f'), showarrow=False)
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
        text=values, textposition='outside', textfont=dict(size=11, color='#1e3a5f'),
        hovertemplate='%{y}: %{x}회<extra></extra>'
    )])
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=40), height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=12, color='#334155')), bargap=0.3,
    )
    return fig

# =============================================================================
# PDF 생성
# =============================================================================
def generate_pdf_report(video_info, total, pos, neu, neg, pos_pct, neg_pct, keywords, top_pos_comments, top_neg_comments, marketing_analysis):
    """PDF 리포트 생성"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import urllib.request
    import os
    
    # 한글 폰트 설정 (Noto Sans KR)
    font_path = '/tmp/NotoSansKR-Regular.ttf'
    font_bold_path = '/tmp/NotoSansKR-Bold.ttf'
    
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(
                'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Regular.ttf',
                font_path
            )
            urllib.request.urlretrieve(
                'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Bold.ttf',
                font_bold_path
            )
        except:
            pass
    
    try:
        pdfmetrics.registerFont(TTFont('NotoSansKR', font_path))
        pdfmetrics.registerFont(TTFont('NotoSansKR-Bold', font_bold_path))
        font_name = 'NotoSansKR'
        font_bold = 'NotoSansKR-Bold'
    except:
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='KoreanTitle', fontName=font_bold, fontSize=18, textColor=colors.HexColor('#1e3a5f'), spaceAfter=10))
    styles.add(ParagraphStyle(name='KoreanHeading', fontName=font_bold, fontSize=12, textColor=colors.HexColor('#1e3a5f'), spaceBefore=15, spaceAfter=8))
    styles.add(ParagraphStyle(name='KoreanBody', fontName=font_name, fontSize=10, textColor=colors.HexColor('#334155'), leading=16))
    styles.add(ParagraphStyle(name='KoreanSmall', fontName=font_name, fontSize=9, textColor=colors.HexColor('#64748b'), leading=14))
    
    story = []
    
    # 제목
    story.append(Paragraph("유튜브 댓글 인사이트 리포트", styles['KoreanTitle']))
    story.append(Paragraph(f"생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", styles['KoreanSmall']))
    story.append(Spacer(1, 10))
    
    # 영상 정보
    story.append(Paragraph("📺 영상 정보", styles['KoreanHeading']))
    info_data = [
        ['제목', video_info.get('title', '')[:50] + ('...' if len(video_info.get('title', '')) > 50 else '')],
        ['채널', video_info.get('channel', '')],
        ['업로드', video_info.get('upload_date', '')],
        ['조회수', format_num(video_info.get('view_count', 0))],
    ]
    info_table = Table(info_data, colWidths=[60, 400])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # 감성 분석
    story.append(Paragraph("📊 감성 분석 결과", styles['KoreanHeading']))
    sentiment_data = [
        ['분석 댓글', f'{total:,}개', '긍정률', f'{pos_pct:.1f}%'],
        ['긍정', f'{pos:,}개', '부정', f'{neg:,}개'],
    ]
    sent_table = Table(sentiment_data, colWidths=[70, 100, 70, 100])
    sent_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sent_table)
    story.append(Spacer(1, 10))
    
    # 키워드
    story.append(Paragraph("🔑 핵심 키워드", styles['KoreanHeading']))
    if keywords:
        kw_text = ', '.join([f"{k}({v})" for k, v in keywords[:10]])
        story.append(Paragraph(kw_text, styles['KoreanBody']))
    story.append(Spacer(1, 10))
    
    # 마케팅 분석
    story.append(Paragraph("💡 마케터 관점 분석", styles['KoreanHeading']))
    if marketing_analysis:
        # 마크다운 제거
        clean_analysis = marketing_analysis.replace('**', '').replace('▸ ', '• ')
        for para in clean_analysis.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['KoreanBody']))
                story.append(Spacer(1, 5))
    story.append(Spacer(1, 10))
    
    # 주요 댓글
    story.append(Paragraph("💬 주요 긍정 댓글", styles['KoreanHeading']))
    for c in top_pos_comments[:3]:
        text = c['text'][:100] + ('...' if len(c['text']) > 100 else '')
        story.append(Paragraph(f"• \"{text}\" (👍 {c['like_count']:,})", styles['KoreanSmall']))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("💬 주요 부정 댓글", styles['KoreanHeading']))
    for c in top_neg_comments[:3]:
        text = c['text'][:100] + ('...' if len(c['text']) > 100 else '')
        story.append(Paragraph(f"• \"{text}\" (👍 {c['like_count']:,})", styles['KoreanSmall']))
    
    # 푸터
    story.append(Spacer(1, 20))
    story.append(Paragraph("─" * 50, styles['KoreanSmall']))
    story.append(Paragraph("유튜브 댓글 분석기 v7.0 | 자동 생성 리포트", styles['KoreanSmall']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# =============================================================================
# 메인
# =============================================================================
def main():
    # 헤더
    st.markdown('''
    <div class="header">
        <h1>📊 유튜브 댓글 분석기</h1>
        <p>영상 URL을 입력하면 댓글 인사이트를 분석합니다</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 입력 (클릭 시 리프레시)
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        # 입력창 클릭 시 초기화를 위해 key 사용
        if st.session_state.clear_input:
            default_value = ""
            st.session_state.clear_input = False
        else:
            default_value = ""
        
        url = st.text_input(
            "URL", 
            value=default_value,
            placeholder="https://www.youtube.com/watch?v=... (클릭하면 초기화됩니다)", 
            label_visibility="collapsed",
            key="url_input"
        )
        
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            btn = st.button("🔍 분석 시작", use_container_width=True)
        with col_btn2:
            if st.button("🔄 초기화", use_container_width=True):
                st.session_state.clear_input = True
                st.session_state.analysis_done = False
                st.rerun()
    
    if btn and url:
        vid = extract_video_id(url)
        if not vid:
            st.error("❌ 유효하지 않은 URL입니다.")
            return
        
        try:
            progress = st.progress(0, "댓글 수집 중...")
            video_info, comments = collect_comments(url, CONFIG["max_comments"])
            progress.progress(50, "분석 중...")
            
            if not video_info or not comments:
                st.warning("⚠️ 댓글을 가져올 수 없습니다.")
                return
            
            df = pd.DataFrame(comments)
            results = [analyze_sentiment(str(t)) for t in df['text'].fillna('')]
            df['sentiment'] = [r[0] for r in results]
            
            keywords = extract_keywords(df['text'].tolist(), CONFIG["top_keywords_count"])
            progress.progress(100, "완료!")
            progress.empty()
            
            # 결과 계산
            total = len(df)
            pos = int((df['sentiment'] == 'positive').sum())
            neu = int((df['sentiment'] == 'neutral').sum())
            neg = int((df['sentiment'] == 'negative').sum())
            pos_pct = pos / total * 100 if total else 0
            neg_pct = neg / total * 100 if total else 0
            
            # 마케팅 분석 생성
            marketing_analysis = generate_keyword_marketing_analysis(keywords, pos_pct, neg_pct, total)
            
            # 주요 댓글
            top_pos_df = df[df['sentiment'] == 'positive'].nlargest(3, 'like_count')
            top_neg_df = df[df['sentiment'] == 'negative'].nlargest(3, 'like_count')
            top_pos_comments = top_pos_df.to_dict('records')
            top_neg_comments = top_neg_df.to_dict('records')
            
            # ========== 영상 정보 박스 ==========
            st.markdown('<div class="video-info-box">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2.5])
            with c1:
                if video_info.get('thumbnail'):
                    st.image(video_info['thumbnail'], use_container_width=True)
            with c2:
                st.markdown(f"### {video_info.get('title', '')}")
                st.markdown(f'''
                <div class="video-info-row">
                    <span class="video-info-label">채널명</span>
                    <span class="video-info-value">{video_info.get('channel', '정보 없음')}</span>
                </div>
                <div class="video-info-row">
                    <span class="video-info-label">업로드 날짜</span>
                    <span class="video-info-value">{video_info.get('upload_date', '정보 없음')}</span>
                </div>
                <div class="video-info-row">
                    <span class="video-info-label">조회수</span>
                    <span class="video-info-value">{format_num(video_info.get('view_count', 0))}</span>
                </div>
                <div class="video-info-row">
                    <span class="video-info-label">좋아요</span>
                    <span class="video-info-value">{format_num(video_info.get('like_count', 0))}</span>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 지표
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("분석 댓글", f"{total:,}개")
            c2.metric("긍정률", f"{pos_pct:.1f}%")
            c3.metric("중립", f"{neu:,}개")
            c4.metric("부정률", f"{neg_pct:.1f}%")
            
            # PDF 다운로드 버튼
            try:
                pdf_buffer = generate_pdf_report(
                    video_info, total, pos, neu, neg, pos_pct, neg_pct,
                    keywords, top_pos_comments, top_neg_comments, marketing_analysis
                )
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_buffer,
                    file_name=f"youtube_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.caption(f"PDF 생성 불가: {e}")
            
            # 차트
            st.markdown('<div class="section-title">📊 분석 결과</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**감성 분포**")
                st.plotly_chart(create_donut_chart(pos, neu, neg), use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**핵심 키워드**")
                kw_chart = create_keyword_chart(keywords)
                if kw_chart:
                    st.plotly_chart(kw_chart, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 키워드 마케팅 분석
            if marketing_analysis:
                st.markdown('<div class="section-title">🎯 키워드 마케팅 분석</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card"><div class="keyword-analysis-text">{marketing_analysis}</div></div>', unsafe_allow_html=True)
            
            # 인사이트
            st.markdown('<div class="section-title">💡 핵심 인사이트</div>', unsafe_allow_html=True)
            
            top_liked = df.nlargest(min(20, len(df)), 'like_count')
            top_pos_r = (top_liked['sentiment'] == 'positive').sum() / max(len(top_liked), 1) * 100
            
            if pos_pct > 60:
                st.markdown(f'''<div class="insight">
                    <div class="insight-title">🌟 강력한 팬덤 기반의 긍정적 바이럴 잠재력</div>
                    <div class="insight-desc">전체 댓글의 <b>{pos_pct:.0f}%</b>가 긍정적입니다. 좋아요 상위 댓글의 <b>{top_pos_r:.0f}%</b>가 긍정인 점은 여론 주도층이 우호적이라는 신호입니다.</div>
                    <div class="insight-action">→ UGC 캠페인, 팬 참여형 챌린지 전략 권장</div>
                </div>''', unsafe_allow_html=True)
            elif pos_pct > 40:
                st.markdown(f'''<div class="insight">
                    <div class="insight-title">📈 호의적이나 열성 팬 전환 필요</div>
                    <div class="insight-desc">긍정 비율 <b>{pos_pct:.0f}%</b>는 좋은 수치이나, 가벼운 관심층이 많을 수 있습니다.</div>
                    <div class="insight-action">→ 비하인드, 팬서비스 콘텐츠로 관계 심화 필요</div>
                </div>''', unsafe_allow_html=True)
            
            if neg_pct > 20:
                st.markdown(f'''<div class="insight">
                    <div class="insight-title">⚠️ 부정 여론 파악 필요</div>
                    <div class="insight-desc">부정 반응이 <b>{neg_pct:.0f}%</b>입니다. 원인 파악이 필요합니다.</div>
                    <div class="insight-action">→ 부정 댓글 분석 후 해명/개선 영역 식별</div>
                </div>''', unsafe_allow_html=True)
            
            # 댓글
            st.markdown('<div class="section-title">💬 주요 댓글</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("**👍 긍정 TOP 3**")
                for c in top_pos_comments:
                    txt = str(c['text'])[:120] + ('...' if len(str(c['text'])) > 120 else '')
                    st.markdown(f'''<div class="comment pos">
                        <div class="comment-text">"{txt}"</div>
                        <div class="comment-likes">👍 {int(c['like_count']):,}</div>
                    </div>''', unsafe_allow_html=True)
            
            with c2:
                st.markdown("**👎 부정 TOP 3**")
                if top_neg_comments:
                    for c in top_neg_comments:
                        txt = str(c['text'])[:120] + ('...' if len(str(c['text'])) > 120 else '')
                        st.markdown(f'''<div class="comment neg">
                            <div class="comment-text">"{txt}"</div>
                            <div class="comment-likes">👍 {int(c['like_count']):,}</div>
                        </div>''', unsafe_allow_html=True)
                else:
                    st.success("🎉 부정 댓글이 거의 없습니다!")
            
            st.markdown('<div class="footer">유튜브 댓글 분석기 v7.0</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    main()
