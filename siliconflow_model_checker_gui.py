import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import threading
import json

# --- API 配置 ---
MODELS_API_URL = "https://api.siliconflow.cn/v1/models"
DEFAULT_API_KEY = "sk-leirgmdwwghisduaqjbuxbetxcnpdypn" # 默认 API Key

# --- 主应用类 ---
class SiliconFlowModelCheckerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # 修改窗口标题
        self.title("SiliconFlow 模型检测器 (文生图 & TTS)")
        # 增加窗口高度以容纳两个列表
        self.geometry("500x700")

        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- API Key 输入 ---
        api_frame = ttk.LabelFrame(main_frame, text="API Key", padding="5")
        api_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- 检测按钮 ---
        check_button = ttk.Button(main_frame, text="检测可用模型", command=self._start_check_thread)
        check_button.pack(pady=10)

        # --- 创建一个 PanedWindow 来分割两个列表 ---
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- 文生图模型列表显示 ---
        image_result_frame = ttk.LabelFrame(paned_window, text="可用文生图模型列表", padding="5", height=250) # 设置初始高度
        image_result_frame.pack_propagate(False) # 防止内部控件撑开框架
        paned_window.add(image_result_frame, weight=1) # 添加到 PanedWindow
        self.image_result_text = scrolledtext.ScrolledText(image_result_frame, wrap=tk.WORD, state=tk.DISABLED) # 初始禁用编辑
        self.image_result_text.pack(fill=tk.BOTH, expand=True)

        # --- 文本转语音模型列表显示 ---
        tts_result_frame = ttk.LabelFrame(paned_window, text="可用文本转语音 (TTS) 模型列表", padding="5", height=250) # 设置初始高度
        tts_result_frame.pack_propagate(False) # 防止内部控件撑开框架
        paned_window.add(tts_result_frame, weight=1) # 添加到 PanedWindow
        self.tts_result_text = scrolledtext.ScrolledText(tts_result_frame, wrap=tk.WORD, state=tk.DISABLED) # 初始禁用编辑
        self.tts_result_text.pack(fill=tk.BOTH, expand=True)

        # --- 状态栏 ---
        self.status_label = ttk.Label(main_frame, text="状态：准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def _set_status(self, message):
        """更新状态栏信息"""
        self.status_label.config(text=f"状态：{message}")
        self.update_idletasks() # 强制更新界面

    def _start_check_thread(self):
        """启动一个新线程来执行API请求，避免阻塞GUI"""
        api_key = self.api_key.get()

        if not api_key:
            messagebox.showerror("错误", "请输入 API Key。")
            return

        self._set_status("正在检测模型...")
        # 清空两个文本框
        self.image_result_text.config(state=tk.NORMAL)
        self.image_result_text.delete('1.0', tk.END)
        self.image_result_text.config(state=tk.DISABLED)
        self.tts_result_text.config(state=tk.NORMAL)
        self.tts_result_text.delete('1.0', tk.END)
        self.tts_result_text.config(state=tk.DISABLED)

        # 创建并启动线程
        thread = threading.Thread(target=self._check_models, args=(api_key,), daemon=True)
        thread.start()

    def _check_models(self, api_key):
        """执行 API 调用获取模型列表并分类"""
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.get(MODELS_API_URL, headers=headers, timeout=30)
            response.raise_for_status() # 检查请求是否成功

            models_data = response.json()
            print("--- DEBUG: Full Models API Response ---")
            print(models_data)
            print("--- END DEBUG ---")

            image_models = []
            tts_models = []
            # 假设返回的数据结构是 {'data': [{'id': 'model_name', ...}, ...]}
            if 'data' in models_data and isinstance(models_data['data'], list):
                for model_info in models_data['data']:
                    model_id = model_info.get('id', '').lower()
                    model_id_original = model_info.get('id', '未知ID') # 保留原始大小写

                    # 筛选文生图模型 (更宽松的条件)
                    if 'stable-diffusion' in model_id or 'sdxl' in model_id or 'flux' in model_id or 'kolors' in model_id or 'image' in model_id or 'sd3' in model_id:
                         image_models.append(model_id_original)
                    # 筛选文本转语音模型
                    elif 'audio' in model_id or 'speech' in model_id or 'tts' in model_id or 'voice' in model_id:
                         tts_models.append(model_id_original)

            status_msg = []
            if image_models:
                status_msg.append(f"检测到 {len(image_models)} 个文生图模型")
            if tts_models:
                 status_msg.append(f"检测到 {len(tts_models)} 个 TTS 模型")

            if not status_msg:
                 final_status = "未检测到相关模型或 API 返回格式不符。"
                 messagebox.showwarning("未找到模型", "未能从 API 响应中识别出文生图或 TTS 模型。\n请检查 API Key 或查看控制台输出。")
            else:
                 final_status = "，".join(status_msg) + "。"

            self._set_status(final_status)
            # 在主线程中更新 GUI
            self.after(0, self._display_models, image_models, tts_models)


        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_message += f"\n错误详情: {error_detail}"
                except ValueError:
                    error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message)
            self._set_status("检测失败")
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误: {e}")
            self._set_status("检测失败")

    def _display_models(self, image_models, tts_models):
        """在对应的文本框中显示模型列表"""
        # 显示文生图模型
        self.image_result_text.config(state=tk.NORMAL) # 启用编辑
        self.image_result_text.delete('1.0', tk.END) # 清空旧内容
        if image_models:
            self.image_result_text.insert(tk.END, "\n".join(image_models))
        else:
            self.image_result_text.insert(tk.END, "未找到可用的文生图模型。")
        self.image_result_text.config(state=tk.DISABLED) # 禁用编辑

        # 显示 TTS 模型
        self.tts_result_text.config(state=tk.NORMAL) # 启用编辑
        self.tts_result_text.delete('1.0', tk.END) # 清空旧内容
        if tts_models:
            self.tts_result_text.insert(tk.END, "\n".join(tts_models))
        else:
            self.tts_result_text.insert(tk.END, "未找到可用的文本转语音模型。")
        self.tts_result_text.config(state=tk.DISABLED) # 禁用编辑

# --- 启动应用 ---
if __name__ == "__main__":
    app = SiliconFlowModelCheckerApp()
    app.mainloop()