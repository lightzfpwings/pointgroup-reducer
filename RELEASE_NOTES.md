## v2.4.0 · Smooth page transitions

- Persistent pages slide forward/back with a short 220 ms cubic ease-out transition.
- Navigation is interruptible: rapid clicks continue from current positions and keep only the latest destination. Inputs and results are preserved.
- Relative page geometry follows live window resizing. Input layout updates only when its content size changes; formulas reuse cached images.
- A Smooth transitions / 平滑过渡 / 平滑過渡 switch disables motion immediately.
- Retains transparent formulas and the clipping fixes from v2.3.1.
- 36 source tests plus native GUI navigation, mid-animation resizing, shutdown and frozen GUI/CLI checks gate publication. Manual Windows/macOS motion acceptance and frame-rate profiling remain pending.
- Outer-window maximize/fullscreen animations are controlled by the operating system; this release animates the application pages.

## 简体中文

前进、返回和主页切换加入约 0.2 秒的平滑过渡，连续点击不会累积动画。输入和结果保留，缩放过程中页面实时适应窗口。顶部可关闭“平滑过渡”。保留英文／简体中文／繁体中文切换与公式透明背景。外层窗口的最大化和全屏动画由操作系统控制。

## 繁體中文

前進、返回與首頁切換加入約 0.2 秒的平滑過渡，連續點擊不會累積動畫。輸入與結果保留，縮放過程中頁面即時配合視窗。頂部可關閉「平滑過渡」。保留英文／簡體中文／繁體中文切換與公式透明背景。外層視窗的最大化與全螢幕動畫由作業系統控制。
