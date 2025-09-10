import streamlit as st
import requests
import datetime
import pytz
import re
import pandas as pd
import plotly.express as px

# ────────────── 한국 시간 ──────────────
kst = pytz.timezone('Asia/Seoul')
현재 = datetime.datetime.now(kst)

# ────────────── 권장 섭취량 ──────────────
권장량 = {"에너지(kcal)":2000,"탄수화물(g)":324,"단백질(g)":55,"지방(g)":54,"칼슘(mg)":700}

# ────────────── 급식 데이터 함수 ──────────────
def get_meal(날짜):
    url = (
        "https://open.neis.go.kr/hub/mealServiceDietInfo"
        "?ATPT_OFCDC_SC_CODE=B10"
        "&SD_SCHUL_CODE=7010806"
        "&Type=json"
        "&MLSV_YMD=" + 날짜
    )
    try:
        data = requests.get(url).json()
        return data['mealServiceDietInfo'][1]['row']
    except:
        return []

# ────────────── Streamlit UI ──────────────
st.markdown("<h1 style='text-align:center; color:#FF6F61;'>🍱 상암고 급식 & 영양소 분석</h1>", unsafe_allow_html=True)

# 날짜 선택 위젯
선택날짜 = st.date_input("📅 날짜를 선택하세요", 현재.date())
오늘 = 선택날짜.strftime("%y%m%d")

st.markdown(f"<p style='text-align:center; color:#FFB347;'>선택한 날짜: {선택날짜.strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)

info = get_meal(오늘)
if not info:
    st.error("해당 날짜의 급식 정보가 없습니다.")
else:
    for row in info:
        meal_name = row['MMEAL_SC_NM']
        dish_str = row['DDISH_NM']
        nutr_info = row['NTR_INFO']

        # 데이터 클리닝
        최종 = re.sub(r"[\d\(\).]", "", dish_str.replace("<br/>","\n"))

        # 메뉴 출력 (카드 느낌)
        st.markdown(f"""
        <div style='background-color:#FFF0F5; padding:15px; border-radius:15px; margin-bottom:10px;'>
            <h3>🍽 {meal_name}</h3>
            <pre style='font-size:14px'>{최종.strip()}</pre>
        </div>
        """, unsafe_allow_html=True)

        # 영양 정보 파싱
        영양dict = {}
        for item in nutr_info.split("<br/>"):
            if ":" in item:
                key,val = item.split(":")
                val = val.strip().replace("g","").replace("kcal","").replace("mg","")
                try: 영양dict[key.strip()] = float(val)
                except: pass

        if 영양dict:
            df = pd.DataFrame(list(영양dict.items()), columns=["영양소","값"])
            st.dataframe(df, use_container_width=True)

            # 권장량 대비 비율
            비교 = []
            for k,v in 영양dict.items():
                if k in 권장량:
                    비교.append([k,v,권장량[k],f"{round(v/권장량[k]*100,1)}%"])
            if 비교:
                st.markdown("✅ **권장량 대비 비율**")
                st.table(pd.DataFrame(비교, columns=["영양소","급식 제공량","권장량","충족률"]))

            # ────────────── Plotly 그래프 ──────────────
            fig = px.bar(
                df,
                x="영양소",
                y="값",
                title=f"{meal_name} 영양 성분",
                color="영양소",
                text="값",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(title_font=dict(size=20, color="#FF69B4"))
            st.plotly_chart(fig, use_container_width=True)

# ────────────── 지난 7일 평균 ──────────────
st.header("📊 지난 7일 평균 영양소 분석")
누적,count = {},0
for i in range(7):
    날짜 = (현재 - datetime.timedelta(days=i)).strftime("%y%m%d")
    rows = get_meal(날짜)
    for row in rows:
        for item in row['NTR_INFO'].split("<br/>"):
            if ":" in item:
                key,val = item.split(":")
                val = val.strip().replace("g","").replace("kcal","").replace("mg","")
                try: 누적[key.strip()] = 누적.get(key.strip(),0)+float(val)
                except: pass
    count+=1

if 누적 and count>0:
    평균 = {k:round(v/count,1) for k,v in 누적.items()}
    df_avg = pd.DataFrame(list(평균.items()), columns=["영양소","평균값"])
    st.dataframe(df_avg,use_container_width=True)

    # ────────────── Plotly 그래프 ──────────────
    fig = px.bar(
        df_avg,
        x="영양소",
        y="평균값",
        title="지난 7일 평균 영양소",
        color="영양소",
        text="평균값",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(title_font=dict(size=20, color="#FF69B4"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("지난 7일간 영양소 데이터를 불러올 수 없습니다.")

# ────────────── 제작자 표시 ──────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>👩‍💻 제작자: 30502 김도현</p>", unsafe_allow_html=True)

