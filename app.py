import streamlit as st
import openai
import json
import re

# ページ設定
st.set_page_config(page_title="韓国語・英語 AI 添削チャット", layout="centered")

# サイドバー設定
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input("OpenAI APIキー", type="password")
    if api_key: openai.api_key = api_key

st.title("KRUS 韓国語・英語 AI 添削チャット")

lang = st.selectbox("学習したい言語を選んでください", ["韓国語", "英語"])
style = st.radio("添削スタイルを選んでください", ["敬語（丁寧な表現）", "タメ口（親しい表現）"], horizontal=True)

user_input = st.text_area("添削したい文章を入力してください", placeholder="例: 안녕하세요. 私は日本人です。")

if st.button("添削する"):
    if not api_key:
        st.error("APIキーを入力してください")
    elif not user_input:
        st.warning("文章を入力してください")
    else:
        with st.spinner("AIが添削しています..."):
            style_instruction = "敬語（저/습니다）" if style == "敬語（丁寧な表現）" else "タメ口（ナ/어/야）"
            
            prompt = f"""
            あなたは優秀な語学教師です。以下の入力を{lang}として添削してください。
            【厳守ルール】:
            1. スタイル: {style}（{style_instruction}）。
            2. 回答構成:
               - 「修正文：」から始める一行の修正結果。
               - 日本語での解説。
               - 最後に重要単語リストをJSON形式で出力。
            3. 重要単語リスト詳細:
               - word: 必ず「ハングル（韓国語文字）」で記述。
               - pronunciation: 必ず「英文字（アルファベット/ローマ字）」で記述。カタカナは絶対に禁止。
               - meaning: 日本語での意味。
            
            JSON形式例（この形式のみを出力）:
            {{"words": [{{"word": "한글", "pronunciation": "hangeul", "meaning": "ハングル"}}]}}
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]
            )
            
            full_text = response.choices[0].message.content
            
            # JSON抽出ロジック（コードブロックや余計な文字を強力に除去）
            words_data = None
            explanation = full_text
            
            # ```json や ``` を除去
            clean_json_text = re.sub(r'```json|```', '', full_text).strip()
            
            start_idx = clean_json_text.find('{')
            end_idx = clean_json_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = clean_json_text[start_idx:end_idx+1]
                try:
                    words_data = json.loads(json_str)
                    explanation = clean_json_text[:start_idx].strip()
                except:
                    pass

            # 修正文の抽出
            fixed_sentence = ""
            for line in explanation.split('\n'):
                if "修正文：" in line:
                    fixed_sentence = line.replace("修正文：", "").strip()
                    break
            if not fixed_sentence: fixed_sentence = explanation.split('\n')[0]
            safe_sentence = fixed_sentence.replace('"', '\\"').replace("'", "\\'").replace("\n", " ")

            # 表示
            st.subheader("AIの添削とアドバイス")
            st.write(explanation)

            st.divider()
            st.write("🌿 音声を選んで聴いてみよう！")

            js_audio_html = f"""
                <style>
                .speed-btn {{
                    padding: 12px 24px !important;
                    margin-right: 10px !important;
                    border-radius: 50px !important;
                    border: 2px solid #4CAF50 !important;
                    background-color: white !important;
                    color: #2E7D32 !important;
                    font-size: 14px !important;
                    font-weight: bold !important;
                    cursor: pointer !important;
                    transition: 0.3s !important;
                }}
                .speed-btn:hover {{ background-color: #e8f5e9 !important; }}
                .speed-btn.active {{ background-color: #4CAF50 !important; color: white !important; }}
                </style>
                <div id="audio-ui">
                    <button onclick="playWithSpeed(0.5, 'btn-05')" class="speed-btn" id="btn-05">0.5x 超スロー</button>
                    <button onclick="playWithSpeed(0.8, 'btn-08')" class="speed-btn" id="btn-08">0.8x ゆっくり</button>
                    <button onclick="playWithSpeed(1.0, 'btn-10')" class="speed-btn active" id="btn-10">1.0x 標準</button>
                </div>
                <script>
                function playWithSpeed(speed, btnId) {{
                    document.querySelectorAll('.speed-btn').forEach(btn => btn.classList.remove('active'));
                    document.getElementById(btnId).classList.add('active');
                    window.speechSynthesis.cancel();
                    const uttr = new SpeechSynthesisUtterance("{safe_sentence}");
                    uttr.lang = "{ 'ko-KR' if lang == '韓国語' else 'en-US' }";
                    uttr.rate = speed;
                    window.speechSynthesis.speak(uttr);
                }}
                </script>
            """
            st.components.v1.html(js_audio_html, height=100)

            if words_data and "words" in words_data:
                st.divider()
                st.subheader("📚 重要単語（単語帳）")
                st.table(words_data["words"])
