import streamlit as st
import openai
import json
import re

st.set_page_config(page_title="韓国語・英語 AI 添削チャット", layout="centered")

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
            prompt = f"""あなたは語学教師です。{lang}として添削して。構成：修正文（一行）、解説、JSON単語リスト。読みはアルファベット。"""
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]
            )
            full_text = response.choices[0].message.content
            words_data = None
            clean_json_text = re.sub(r'```json|```', '', full_text).strip()
            start_idx = clean_json_text.find('{')
            end_idx = clean_json_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                try:
                    words_data = json.loads(clean_json_text[start_idx:end_idx+1])
                    explanation = clean_json_text[:start_idx].strip()
                except: explanation = full_text
            else: explanation = full_text

            fixed_sentence = ""
            for line in explanation.split('\n'):
                if "修正文：" in line:
                    fixed_sentence = line.replace("修正文：", "").strip()
                    break
            if not fixed_sentence: fixed_sentence = explanation.split('\n')[0]
            safe_sentence = fixed_sentence.replace('"', '\\"').replace("'", "\\'").replace("\n", " ")

            st.subheader("AIの添削とアドバイス")
            st.write(explanation)

            st.divider()
            st.write("🌿 音声再生（速度を選んでください）")

            # モバイルで確実に速度を反映させるための構造変更
            js_audio_html = f"""
                <style>
                .speed-btn {{ padding: 12px 20px; margin-right: 8px; border-radius: 50px; border: 2px solid #4CAF50; background: white; color: #2E7D32; font-size: 14px; font-weight: bold; cursor: pointer; }}
                .speed-btn.active {{ background: #4CAF50; color: white; }}
                </style>
                <div id="audio-ui">
                    <button onclick="changeSpeed(0.5, 'btn-05')" class="speed-btn" id="btn-05">0.5x</button>
                    <button onclick="changeSpeed(0.8, 'btn-08')" class="speed-btn" id="btn-08">0.8x</button>
                    <button onclick="changeSpeed(1.0, 'btn-10')" class="speed-btn active" id="btn-10">1.0x</button>
                </div>
                <script>
                var currentRate = 1.0;
                function changeSpeed(speed, btnId) {{
                    currentRate = parseFloat(speed);
                    document.querySelectorAll('.speed-btn').forEach(btn => btn.classList.remove('active'));
                    document.getElementById(btnId).classList.add('active');
                    playSpeech(); // 速度変更時に即再生
                }}
                function playSpeech() {{
                    window.speechSynthesis.cancel();
                    // iOS対策：発話オブジェクトを再生直前に都度生成し、明示的にプロパティを代入
                    var msg = new SpeechSynthesisUtterance();
                    msg.text = "{safe_sentence}";
                    msg.lang = "{ 'ko-KR' if lang == '韓国語' else 'en-US' }";
                    msg.rate = currentRate;
                    window.speechSynthesis.speak(msg);
                }}
                </script>
            """
            st.components.v1.html(js_audio_html, height=100)

            if words_data and "words" in words_data:
                st.divider()
                st.subheader("📚 重要単語（単語帳）")
                st.table(words_data["words"])
