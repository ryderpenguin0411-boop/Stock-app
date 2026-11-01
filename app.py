# ==========================================
# 頁面 A：歡迎封面頁（Welcome Screen）
# ==========================================
if st.session_state.page == "welcome":
    # 建立左右留白欄位，讓圖片置中
    col_left, col_mid, col_right = st.columns([1, 6, 1])

    with col_mid:
        try:
            # 顯示你上傳的手繪首頁圖
            st.image("IMG_0865.jpeg", use_container_width=True)
        except Exception:
            st.warning("請確認 GitHub 上是否有 IMG_0865.jpeg 圖片檔案。")

        # 緊貼在圖片下方的簡約按鈕
        st.write("")  # 微調間距
        if st.button("👉 進入看盤系統 (CONTINUE)", use_container_width=True, key="btn_continue"):
            st.session_state.page = "dashboard"
            st.rerun()
