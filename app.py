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
            
            prompt = f"""
            あなたは優秀な語学教師です。以下の入力を{lang}として添削してください。
            【厳守ルール】:
            1. スタイル: {style}（{style_instruction}）。
            2. 回答構成:
               - 「修正文：」から始める一行。
               - 日本語での解説。
               - 最後に重要単語リスト（JSON形式）。
            3. 単語リスト詳細:
               - word: 必ず「ハングル」
               - pronunciation: 必ず「アルファベット（ローマ字）」
               - meaning: 日本語での意味
            JSON形式例：{{"words": [{{"word": "한글", "pronunciation": "hangeul", "meaning": "ハングル"}}]}}
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]
            )
            
            full_text = response.choices[0].message.content
            
            # JSON抽出ロジック（強化版）
            words_data = None
            explanation = full_text
            clean_text = re.sub(r'```json|```', '', full_text).strip()
            start_idx = clean_text.find('{')
            end_idx = clean_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                try:
                    json_str = clean_text[start_idx:end_idx+1]
                    words_data = json.loads(json_str)
                    explanation = clean_text[:start_idx].strip()
                except:
                    pass

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
            st.write("🌿 音声再生（速度を選ぶと再生します）")

            # スマホ対応：発話オブジェクトを完全にリセットしてから再生するJS
            js_audio_html = f"""
                <style>
                .speed-btn {{
                    padding: 12px 18px !important;
                    margin-right: 5px !important;
                    border-radius: 50px !important;
                    border: 2px solid #4CAF50 !important;
                    background-color: white !important;
                    color: #2E7D32 !important;
                    font-size: 14px !important;
                    font-weight: bold !important;
                }}
                .active {{ background-color: #4CAF50 !important; color: white !important; }}
                </style>
                <div id="audio-ui">
                    <button onclick="playWithSpeed(0.5, 'btn-05')" class="speed-btn" id="btn-05">0.5x</button>
                    <button onclick="playWithSpeed(0.8, 'btn-08')" class="speed-btn" id="btn-08">0.8x</button>
                    <button onclick="playWithSpeed(1.0, 'btn-10')" class="speed-btn active" id="btn-10">1.0x</button>
                </div>
                <script>
                function playWithSpeed(rate, btnId) {{
                    document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
                    document.getElementById(btnId).classList.add('active');
                    
                    // 音声リストを完全にクリア
                    window.speechSynthesis.cancel();
                    
                    // スマホSafari対策：わずかな遅延を置いてから新規作成
                    setTimeout(() => {{
                        var utterance = new SpeechSynthesisUtterance("{safe_sentence}");
                        utterance.lang = "{ 'ko-KR' if lang == '韓国語' else 'en-US' }";
                        utterance.rate = parseFloat(rate);
                        window.speechSynthesis.speak(utterance);
                    }}, 100);
                }}
                </script>
            """
            st.components.v1.html(js_audio_html, height=100)

            if words_data and "words" in words_data:
                st.divider()
                st.subheader("📚 重要単語（単語帳）")
                st.table(words_data["words"])
