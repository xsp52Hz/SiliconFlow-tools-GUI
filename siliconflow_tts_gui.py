import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import threading
import os
import tempfile
import subprocess # Added for cross-platform play

# --- API 配置 ---
API_URL = "https://api.siliconflow.cn/v1/audio/speech" #
MODELS = { # 基于搜索结果 和
    "FunAudioLLM/CosyVoice2-0.5B": [
        "alex", "benjamin", "charles", "david", # 男声
        "anna", "bella", "claire", "diana"      # 女声
    ]
    # 未来可以添加更多模型
}
DEFAULT_MODEL = "FunAudioLLM/CosyVoice2-0.5B"
DEFAULT_VOICE = "alex"
OUTPUT_FORMATS = ["mp3", "wav", "opus", "pcm"] #
DEFAULT_FORMAT = "mp3"
DEFAULT_API_KEY = "sk-leirgmdwwghis" # 添加默认 API Key

# --- 主应用类 ---
class SiliconFlowTTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SiliconFlow 文本转语音 GUI")
        self.geometry("600x650")
        self.resizable(False, False)

        # 设置默认 API Key
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.voice_var = tk.StringVar(value=DEFAULT_VOICE)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.gain_var = tk.DoubleVar(value=0.0)
        self.format_var = tk.StringVar(value=DEFAULT_FORMAT)
        self.audio_data = None # 用于存储生成的音频数据

        self._create_widgets()
        self._update_voice_options() # 初始化音色选项

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- API Key ---
        api_frame = ttk.LabelFrame(main_frame, text="API Key", padding="5")
        api_frame.pack(fill=tk.X, pady=5)
        # API Key 输入框现在会显示默认值
        ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- 文本输入 ---
        text_frame = ttk.LabelFrame(main_frame, text="输入文本", padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_input = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10, width=70)
        self.text_input.pack(fill=tk.BOTH, expand=True)

        # --- 参数设置 ---
        params_frame = ttk.Frame(main_frame, padding="5")
        params_frame.pack(fill=tk.X, pady=5)

        # 模型选择
        model_label = ttk.Label(params_frame, text="模型:")
        model_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_menu = ttk.Combobox(params_frame, textvariable=self.model_var, values=list(MODELS.keys()), state="readonly", width=25)
        self.model_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.model_menu.bind("<<ComboboxSelected>>", self._update_voice_options)

        # 音色选择
        voice_label = ttk.Label(params_frame, text="音色:")
        voice_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.voice_menu = ttk.Combobox(params_frame, textvariable=self.voice_var, state="readonly", width=15)
        self.voice_menu.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # 语速
        speed_label = ttk.Label(params_frame, text="语速 (0.25-4.0):")
        speed_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        speed_scale = ttk.Scale(params_frame, from_=0.25, to=4.0, variable=self.speed_var, orient=tk.HORIZONTAL, length=150)
        speed_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        speed_value_label = ttk.Label(params_frame, textvariable=self.speed_var) # 显示当前值
        speed_value_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)


        # 音量 (增益)
        gain_label = ttk.Label(params_frame, text="增益 (-10-10 dB):")
        gain_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        gain_scale = ttk.Scale(params_frame, from_=-10.0, to=10.0, variable=self.gain_var, orient=tk.HORIZONTAL, length=150)
        gain_scale.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        gain_value_label = ttk.Label(params_frame, textvariable=self.gain_var) # 显示当前值
        gain_value_label.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)


        # 输出格式
        format_label = ttk.Label(params_frame, text="格式:")
        format_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        format_menu = ttk.Combobox(params_frame, textvariable=self.format_var, values=OUTPUT_FORMATS, state="readonly", width=10)
        format_menu.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # --- 按钮和状态 ---
        action_frame = ttk.Frame(main_frame, padding="5")
        action_frame.pack(fill=tk.X, pady=10)

        self.generate_button = ttk.Button(action_frame, text="生成语音", command=self._start_generate_thread, width=15)
        self.generate_button.pack(side=tk.LEFT, padx=10)

        self.play_button = ttk.Button(action_frame, text="播放", command=self._play_audio, state=tk.DISABLED, width=15)
        self.play_button.pack(side=tk.LEFT, padx=10)

        self.save_button = ttk.Button(action_frame, text="保存", command=self._save_audio, state=tk.DISABLED, width=15)
        self.save_button.pack(side=tk.LEFT, padx=10)

        self.status_label = ttk.Label(main_frame, text="状态：准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def _update_voice_options(self, event=None):
        """根据选择的模型更新音色下拉菜单"""
        selected_model = self.model_var.get()
        voices = MODELS.get(selected_model, [])
        self.voice_menu['values'] = voices
        if voices:
            # 如果当前音色不在新列表里，则设为第一个
            if self.voice_var.get() not in voices:
                self.voice_var.set(voices)
        else:
            self.voice_var.set("") # 没有可选音色

    def _set_status(self, message):
        """更新状态栏信息"""
        self.status_label.config(text=f"状态：{message}")
        self.update_idletasks() # 强制更新界面

    def _toggle_buttons(self, enable):
        """启用或禁用按钮"""
        state = tk.NORMAL if enable else tk.DISABLED
        self.generate_button.config(state=state)
        # 只有生成成功后才启用播放和保存
        play_save_state = tk.NORMAL if enable and self.audio_data else tk.DISABLED
        self.play_button.config(state=play_save_state)
        self.save_button.config(state=play_save_state)

    def _start_generate_thread(self):
        """启动一个新线程来执行API请求，避免阻塞GUI"""
        api_key = self.api_key.get()
        text = self.text_input.get("1.0", tk.END).strip()

        if not api_key:
            messagebox.showerror("错误", "请输入 API Key。")
            return
        if not text:
            messagebox.showerror("错误", "请输入要转换的文本。")
            return

        self._set_status("正在生成语音...")
        self._toggle_buttons(False) # 禁用按钮
        self.audio_data = None # 清除旧数据

        # 创建并启动线程
        thread = threading.Thread(target=self._generate_speech, args=(api_key, text), daemon=True)
        thread.start()

    def _generate_speech(self, api_key, text):
        """执行API调用"""
        model = self.model_var.get()
        voice_name = self.voice_var.get()
        # API 需要的 voice 格式是 "模型名:音色名"
        full_voice_id = f"{model}:{voice_name}"
        speed = self.speed_var.get()
        gain = self.gain_var.get()
        response_format = self.format_var.get()

        payload = {
            "model": model,
            "input": text,
            "voice": full_voice_id,
            "response_format": response_format,
            "speed": speed,
            "gain": gain,
            "stream": False # GUI应用通常不需要流式 (设为False获取完整数据)
            # sample_rate 可以根据需要添加，但API文档说会根据格式有默认值
        }
        headers = {
            "Authorization": f"Bearer {api_key}", #
            "Content-Type": "application/json" #
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60) # 增加超时时间
            response.raise_for_status() # 如果状态码不是 2xx，则抛出异常

            self.audio_data = response.content # 保存二进制音频数据
            self._set_status(f"语音生成成功！({len(self.audio_data)} bytes)")

        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json() # 尝试解析JSON错误信息
                    error_message += f"\n错误详情: {error_detail}"
                except ValueError: # JSON解析失败
                    error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message)
            self._set_status("生成失败")
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误: {e}")
            self._set_status("生成失败")
        finally:
            # 无论成功失败，都要在主线程中重新启用按钮
            self.after(0, self._toggle_buttons, True)


    def _play_audio(self):
        """播放生成的音频 (使用临时文件和系统默认播放器)"""
        if not self.audio_data:
            messagebox.showwarning("警告", "没有可播放的音频数据。请先生成语音。")
            return

        try:
            # 创建临时文件
            file_extension = self.format_var.get()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_audio_file:
                temp_audio_file.write(self.audio_data)
                temp_file_path = temp_audio_file.name

            self._set_status(f"正在尝试播放临时文件: {temp_file_path}")

            # 尝试使用系统默认程序打开音频文件
            # 注意：这依赖于操作系统正确配置了文件关联
            if os.name == 'nt': # Windows
                os.startfile(temp_file_path)
            elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin': # macOS Check added for safety
                subprocess.call(['open', temp_file_path])
            else: # Linux and other Unix-like
                subprocess.call(['xdg-open', temp_file_path])

            # 注意：我们无法直接知道播放是否成功或何时结束
            # 可以在播放后删除临时文件，但这可能导致播放器刚打开就找不到文件
            # 一个折衷方案是让用户手动管理临时文件，或者在程序退出时清理
            # 这里暂时不删除

        except Exception as e:
            messagebox.showerror("播放错误", f"无法播放音频文件: {e}")
            self._set_status("播放失败")


    def _save_audio(self):
        """保存生成的音频文件"""
        if not self.audio_data:
            messagebox.showwarning("警告", "没有可保存的音频数据。请先生成语音。")
            return

        file_extension = self.format_var.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_extension}",
            filetypes=[(f"{file_extension.upper()} 文件", f"*.{file_extension}"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "wb") as f:
                    f.write(self.audio_data)
                self._set_status(f"音频已保存到: {file_path}")
                messagebox.showinfo("成功", f"音频文件已成功保存到\n{file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"无法保存文件: {e}")
                self._set_status("保存失败")
        else:
            self._set_status("保存操作已取消")

# --- 启动应用 ---
if __name__ == "__main__":
    app = SiliconFlowTTSApp()
    app.mainloop()