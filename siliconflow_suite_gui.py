import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import threading
import os
import tempfile
import subprocess
import json
import re
from PIL import Image, ImageTk
import io
import base64 # 确保导入 base64

# --- 全局配置 ---
DEFAULT_API_KEY = "sk-leirgmdwwghisduaqjbuxbetxcnpdypnpxpnpyco"
MODELS_LIST_API_URL = "https://api.siliconflow.cn/v1/models" # 模型列表 API

# --- 文生图配置 ---
IMAGE_API_URL = "https://api.siliconflow.cn/v1/images/generations"
INITIAL_IMAGE_MODELS = [
    "Kwai-Kolors/Kolors",
    "black-forest-labs/FLUX.1-schnell",
    "black-forest-labs/FLUX.1-dev",
    "Pro/black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-3-5-large",
    "black-forest-labs/FLUX.1-pro",
    "LoRA/black-forest-labs/FLUX.1-dev",
    "stabilityai/stable-diffusion-xl-base-1.0",
]
DEFAULT_IMAGE_MODEL = "Kwai-Kolors/Kolors"
IMAGE_SIZES = [
    "1024x1024", "512x512", "1024x768", "768x1024", "1024x576", "576x1024",
]
DEFAULT_IMAGE_SIZE = "1024x1024"

# --- 文本转语音 (TTS) 配置 ---
TTS_API_URL = "https://api.siliconflow.cn/v1/audio/speech"
FISH_SPEECH_VOICES = ["alex", "anna", "bella", "benjamin", "charles", "claire", "david", "diana"]
INITIAL_TTS_MODELS = {
    "FunAudioLLM/CosyVoice2-0.5B": FISH_SPEECH_VOICES,
    "fishaudio/fish-speech-1.4": FISH_SPEECH_VOICES,
    "fishaudio/fish-speech-1.5": FISH_SPEECH_VOICES,
}
DEFAULT_TTS_MODEL = "FunAudioLLM/CosyVoice2-0.5B"
DEFAULT_TTS_VOICE = "alex"
TTS_OUTPUT_FORMATS = ["mp3", "wav", "opus", "pcm"]
DEFAULT_TTS_FORMAT = "mp3"

# --- 语音转文本 (ASR) 配置 ---
ASR_API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
INITIAL_ASR_MODELS = ["FunAudioLLM/SenseVoiceSmall"]
DEFAULT_ASR_MODEL = "FunAudioLLM/SenseVoiceSmall"
ASR_LANGUAGES = ["zh", "en", "ja", "ko"]
DEFAULT_ASR_LANGUAGE = "zh"


# --- 主应用类 ---
class SiliconFlowSuiteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SiliconFlow 工具套件")
        self.geometry("900x800")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.image_gen_frame = ImageGenFrame(self.notebook, self, INITIAL_IMAGE_MODELS)
        self.tts_frame = TTSFrame(self.notebook, self, INITIAL_TTS_MODELS)
        self.stt_frame = SpeechToTextFrame(self.notebook, self, INITIAL_ASR_MODELS)
        self.model_checker_frame = ModelCheckerFrame(self.notebook, self)

        self.notebook.add(self.image_gen_frame, text='文生图')
        self.notebook.add(self.tts_frame, text='文本转语音 (TTS)')
        self.notebook.add(self.stt_frame, text='语音转文本 (ASR)')
        self.notebook.add(self.model_checker_frame, text='模型检测器')

        self.status_label = ttk.Label(self, text="状态：准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def set_status(self, message):
        self.status_label.config(text=f"状态：{message}")
        self.update_idletasks()

# --- 文生图 Frame 类 ---
class ImageGenFrame(ttk.Frame):
    def __init__(self, parent_notebook, main_app, initial_models):
        super().__init__(parent_notebook, width=800, height=700)
        self.pack_propagate(False); self.main_app = main_app; self.available_models = initial_models
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        default_model = DEFAULT_IMAGE_MODEL if DEFAULT_IMAGE_MODEL in self.available_models else (self.available_models if self.available_models else "")
        self.model_var = tk.StringVar(value=default_model); self.size_var = tk.StringVar(value=DEFAULT_IMAGE_SIZE)
        self.steps_var = tk.IntVar(value=25); self.cfg_scale_var = tk.DoubleVar(value=7.0); self.seed_var = tk.StringVar(value="")
        self.image_data_bytes = None; self.photo_image = None
        self._create_widgets()
    def _create_widgets(self):
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL); paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        control_frame = ttk.Frame(paned_window, width=350); control_frame.pack_propagate(False); paned_window.add(control_frame, weight=1)
        api_frame = ttk.LabelFrame(control_frame, text="API Key", padding="5"); api_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=40, show="*").pack(fill=tk.X, expand=True)
        prompt_frame = ttk.LabelFrame(control_frame, text="Prompt (描述图像)", padding="5"); prompt_frame.pack(fill=tk.X, pady=5, padx=5)
        self.prompt_input = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=6, width=40); self.prompt_input.pack(fill=tk.X, expand=True)
        neg_prompt_frame = ttk.LabelFrame(control_frame, text="Negative Prompt (不希望出现)", padding="5"); neg_prompt_frame.pack(fill=tk.X, pady=5, padx=5)
        self.neg_prompt_input = scrolledtext.ScrolledText(neg_prompt_frame, wrap=tk.WORD, height=4, width=40); self.neg_prompt_input.pack(fill=tk.X, expand=True)
        params_frame = ttk.LabelFrame(control_frame, text="参数设置", padding="5"); params_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(params_frame, text="模型:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_menu = ttk.Combobox(params_frame, textvariable=self.model_var, values=self.available_models, state="readonly", width=35); self.model_menu.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(params_frame, text="尺寸:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        size_menu = ttk.Combobox(params_frame, textvariable=self.size_var, values=IMAGE_SIZES, state="readonly", width=15); size_menu.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(params_frame, text="步数 (Steps):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        steps_spinbox = ttk.Spinbox(params_frame, from_=1, to=100, textvariable=self.steps_var, width=8); steps_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(params_frame, text="引导系数 (CFG):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        cfg_scale = ttk.Scale(params_frame, from_=0.0, to=20.0, variable=self.cfg_scale_var, orient=tk.HORIZONTAL, length=100); cfg_scale.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        cfg_label = ttk.Label(params_frame, textvariable=self.cfg_scale_var); cfg_label.grid(row=3, column=2, padx=2, pady=5, sticky=tk.W)
        ttk.Label(params_frame, text="种子 (Seed):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        seed_entry = ttk.Entry(params_frame, textvariable=self.seed_var, width=15); seed_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(params_frame, text="(留空则随机)").grid(row=5, column=1, columnspan=2, padx=5, pady=2, sticky=tk.W)
        action_frame = ttk.Frame(control_frame, padding="10"); action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        self.generate_button = ttk.Button(action_frame, text="生成图像", command=self._start_generate_thread, width=12); self.generate_button.pack(side=tk.LEFT, padx=10)
        self.save_button = ttk.Button(action_frame, text="保存图像", command=self._save_image, state=tk.DISABLED, width=12); self.save_button.pack(side=tk.RIGHT, padx=10)
        image_frame = ttk.Frame(paned_window); paned_window.add(image_frame, weight=2)
        self.image_label = ttk.Label(image_frame, text="生成的图像将显示在这里", anchor=tk.CENTER, relief=tk.GROOVE); self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    def update_model_list(self, new_models):
        self.available_models = new_models; current_selection = self.model_var.get(); self.model_menu['values'] = self.available_models
        if self.available_models: self.model_var.set(self.available_models if current_selection not in self.available_models else current_selection)
        else: self.model_var.set("")
    def _set_status(self, message): self.main_app.set_status(message)
    def _toggle_buttons(self, enable_generate, enable_save): self.generate_button.config(state=tk.NORMAL if enable_generate else tk.DISABLED); self.save_button.config(state=tk.NORMAL if enable_save else tk.DISABLED)
    def _start_generate_thread(self):
        api_key = self.api_key.get(); prompt = self.prompt_input.get("1.0", tk.END).strip()
        if not api_key: messagebox.showerror("错误", "请输入 API Key。", parent=self); return
        if not prompt: messagebox.showerror("错误", "请输入 Prompt。", parent=self); return
        self._set_status("正在生成图像..."); self._toggle_buttons(False, False); self.image_data_bytes = None; self.image_label.config(image='', text="正在生成..."); self.update_idletasks()
        thread = threading.Thread(target=self._generate_image, args=(api_key, prompt), daemon=True); thread.start()
    def _generate_image(self, api_key, prompt):
        neg_prompt = self.neg_prompt_input.get("1.0", tk.END).strip(); model = self.model_var.get(); size_str = self.size_var.get(); steps = self.steps_var.get(); cfg = self.cfg_scale_var.get(); seed_str = self.seed_var.get()
        try: width, height = map(int, size_str.split('x'))
        except ValueError: messagebox.showerror("错误", "无效的图像尺寸格式。", parent=self); self.after(0, self._set_status, "生成失败：无效尺寸"); self.after(0, self._toggle_buttons, True, False); return
        payload = {"model": model, "prompt": prompt, "n": 1, "width": width, "height": height, "num_inference_steps": steps, "guidance_scale": cfg}
        if neg_prompt: payload["negative_prompt"] = neg_prompt
        if seed_str.isdigit(): payload["seed"] = int(seed_str)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(IMAGE_API_URL, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            result = response.json()
            print("--- DEBUG: Full API Response ---")
            print(result)
            print("--- END DEBUG ---")

            # 整合后的 URL 提取逻辑
            response_text = json.dumps(result)
            image_url = None

            # 尝试从 images 字段获取
            if 'images' in result and isinstance(result['images'], list) and len(result['images']) > 0:
                if isinstance(result['images'][0], dict) and 'url' in result['images'][0]:
                    image_url = result['images'][0]['url']
                    print(f"--- DEBUG: Found URL in images[0]['url']: {image_url}")

            # 如果上面失败，尝试从 data 字段获取
            if not image_url and 'data' in result and isinstance(result['data'], list) and len(result['data']) > 0:
                 if isinstance(result['data'][0], dict) and 'url' in result['data'][0]:
                    image_url = result['data'][0]['url']
                    print(f"--- DEBUG: Found URL in data[0]['url']: {image_url}")

            # 如果还是没找到，尝试直接从响应文本中提取URL
            if not image_url:
                url_matches = re.findall(r'https://[^"\']+\.(?:png|jpg|jpeg|gif)', response_text)
                if url_matches:
                    image_url = url_matches[0] # 取第一个匹配的 URL
                    print(f"--- DEBUG: Extracted URL using regex: {image_url}")

            if image_url:
                self._set_status(f"获取到图像 URL，正在下载...")
                try:
                    print(f"--- DEBUG: Attempting to download image from URL...")
                    print(f"--- DEBUG: URL to download: {image_url}")

                    image_response = requests.get(image_url, timeout=60)
                    image_response.raise_for_status()
                    self.image_data_bytes = image_response.content
                    print(f"--- DEBUG: Image downloaded successfully ({len(self.image_data_bytes)} bytes).")
                    self._set_status("图像下载成功！")
                    self.after(0, self._display_image)
                    self.after(0, self._toggle_buttons, True, True)
                except requests.exceptions.RequestException as img_e:
                    error_msg = f"从 URL 下载图像失败: {img_e}"
                    print(f"--- DEBUG: Image download failed ---")
                    print(f"URL used for download: {image_url}")
                    print(f"Error: {img_e}")
                    print(f"--- END DEBUG ---")
                    messagebox.showerror("下载错误", f"{error_msg}\n\n请检查网络连接或 URL 是否有效。\nURL: {image_url}", parent=self)
                    self.after(0, self._set_status, "图像下载失败")
                    self.after(0, self._toggle_buttons, True, False)
                    self.after(0, self._display_error_in_area, f"下载失败: {error_msg}\nURL: {image_url}") # 在区域显示错误
                except Exception as display_e:
                    messagebox.showerror("处理错误", f"下载或处理图像时出错: {display_e}", parent=self)
                    self.after(0, self._set_status, "图像处理失败")
                    self.after(0, self._toggle_buttons, True, False)
            else:
                error_msg = "无法从 API 响应中提取图像 URL"
                messagebox.showerror("API 错误", f"生成失败: {error_msg}\n\n请检查控制台输出获取详细的 API 响应内容。", parent=self)
                self.after(0, self._set_status, f"生成失败: {error_msg}")
                self.after(0, self._toggle_buttons, True, False)
                self.after(0, self._display_error_in_area, f"生成失败: {error_msg}") # 在区域显示错误

        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_message += f"\n错误详情: {error_detail.get('error', {}).get('message', e.response.text)}"
                except ValueError:
                    error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message, parent=self)
            self.after(0, self._set_status, "生成失败")
            self.after(0, self._toggle_buttons, True, False)
            self.after(0, self._display_error_in_area, f"生成失败: {error_message}") # 在区域显示错误
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误: {e}", parent=self)
            self.after(0, self._set_status, "生成失败")
            self.after(0, self._toggle_buttons, True, False)
            self.after(0, self._display_error_in_area, f"生成失败: {e}") # 在区域显示错误

    def _display_image(self):
        if not self.image_data_bytes: return
        try:
            img = Image.open(io.BytesIO(self.image_data_bytes)); label_width = self.image_label.winfo_width(); label_height = self.image_label.winfo_height()
            if label_width < 10 or label_height < 10: label_width, label_height = 400, 400
            img_copy = img.copy(); img_copy.thumbnail((label_width - 20, label_height - 20), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img_copy); self.image_label.config(image=self.photo_image, text="")
        except Exception as e: messagebox.showerror("显示错误", f"无法显示图像: {e}", parent=self); self.image_label.config(image='', text="无法显示图像"); self._set_status("图像显示失败")

    def _display_error_in_area(self, error_message):
        self.image_label.config(image='', text=f"错误:\n{error_message}", wraplength=self.image_label.winfo_width()-20)

    def _save_image(self):
        if not self.image_data_bytes: messagebox.showwarning("警告", "没有可保存的图像数据。请先生成图像。", parent=self); return
        try: img_format = Image.open(io.BytesIO(self.image_data_bytes)).format; img_format = img_format.lower() if img_format else 'png'
        except Exception: img_format = 'png'
        file_path = filedialog.asksaveasfilename(parent=self, defaultextension=f".{img_format}", filetypes=[(f"{img_format.upper()} 文件", f"*.{img_format}"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, "wb") as f: f.write(self.image_data_bytes)
                self._set_status(f"图像已保存到: {file_path}"); messagebox.showinfo("成功", f"图像文件已成功保存到\n{file_path}", parent=self)
            except Exception as e: messagebox.showerror("保存错误", f"无法保存文件: {e}", parent=self); self._set_status("保存失败")
        else: self._set_status("保存操作已取消")

# --- 文本转语音 (TTS) Frame 类 ---
class TTSFrame(ttk.Frame):
    def __init__(self, parent_notebook, main_app, initial_models_dict):
        super().__init__(parent_notebook, width=800, height=700)
        self.pack_propagate(False); self.main_app = main_app
        self.available_models_dict = initial_models_dict; self.available_model_ids = list(self.available_models_dict.keys())
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        default_model = DEFAULT_TTS_MODEL if DEFAULT_TTS_MODEL in self.available_model_ids else (self.available_model_ids if self.available_model_ids else "")
        self.model_var = tk.StringVar(value=default_model)
        default_voices = self.available_models_dict.get(default_model, []); default_voice = DEFAULT_TTS_VOICE if DEFAULT_TTS_VOICE in default_voices else (default_voices if default_voices else "")
        self.voice_var = tk.StringVar(value=default_voice); self.speed_var = tk.DoubleVar(value=1.0); self.gain_var = tk.DoubleVar(value=0.0); self.format_var = tk.StringVar(value=DEFAULT_TTS_FORMAT)
        self.audio_data = None; self._create_widgets(); self._update_voice_options()
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        api_frame = ttk.LabelFrame(main_frame, text="API Key", padding="5"); api_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        text_frame = ttk.LabelFrame(main_frame, text="输入文本", padding="5"); text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.text_input = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10, width=70); self.text_input.pack(fill=tk.BOTH, expand=True)
        params_frame = ttk.Frame(main_frame, padding="5"); params_frame.pack(fill=tk.X, pady=5)
        model_label = ttk.Label(params_frame, text="模型:"); model_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_menu = ttk.Combobox(params_frame, textvariable=self.model_var, values=self.available_model_ids, state="readonly", width=25); self.model_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W); self.model_menu.bind("<<ComboboxSelected>>", self._update_voice_options)
        voice_label = ttk.Label(params_frame, text="音色:"); voice_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.voice_menu = ttk.Combobox(params_frame, textvariable=self.voice_var, state="readonly", width=15); self.voice_menu.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        speed_label = ttk.Label(params_frame, text="语速 (0.25-4.0):"); speed_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        speed_scale = ttk.Scale(params_frame, from_=0.25, to=4.0, variable=self.speed_var, orient=tk.HORIZONTAL, length=150); speed_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        speed_value_label = ttk.Label(params_frame, textvariable=self.speed_var); speed_value_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        gain_label = ttk.Label(params_frame, text="增益 (-10-10 dB):"); gain_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        gain_scale = ttk.Scale(params_frame, from_=-10.0, to=10.0, variable=self.gain_var, orient=tk.HORIZONTAL, length=150); gain_scale.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        gain_value_label = ttk.Label(params_frame, textvariable=self.gain_var); gain_value_label.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        format_label = ttk.Label(params_frame, text="格式:"); format_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        format_menu = ttk.Combobox(params_frame, textvariable=self.format_var, values=TTS_OUTPUT_FORMATS, state="readonly", width=10); format_menu.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        action_frame = ttk.Frame(main_frame, padding="5"); action_frame.pack(fill=tk.X, pady=10)
        self.generate_button = ttk.Button(action_frame, text="生成语音", command=self._start_generate_thread, width=15); self.generate_button.pack(side=tk.LEFT, padx=10)
        self.play_button = ttk.Button(action_frame, text="播放", command=self._play_audio, state=tk.DISABLED, width=15); self.play_button.pack(side=tk.LEFT, padx=10)
        self.save_button = ttk.Button(action_frame, text="保存", command=self._save_audio, state=tk.DISABLED, width=15); self.save_button.pack(side=tk.LEFT, padx=10)
    def update_model_list(self, new_model_ids):
        self.available_model_ids = new_model_ids; current_selection = self.model_var.get(); self.model_menu['values'] = self.available_model_ids
        if self.available_model_ids:
            if current_selection not in self.available_model_ids: self.model_var.set(self.available_model_ids); self._update_voice_options()
            else: self._update_voice_options()
        else: self.model_var.set(""); self.voice_var.set(""); self.voice_menu['values'] = []
    def _set_status(self, message): self.main_app.set_status(message)
    def _update_voice_options(self, event=None):
        selected_model = self.model_var.get(); voices = INITIAL_TTS_MODELS.get(selected_model, []); self.voice_menu['values'] = voices
        if voices: current_voice = self.voice_var.get(); self.voice_var.set(voices if current_voice not in voices else current_voice)
        else: self.voice_var.set("")
    def _toggle_buttons(self, enable):
        state = tk.NORMAL if enable else tk.DISABLED; self.generate_button.config(state=state)
        play_save_state = tk.NORMAL if enable and self.audio_data else tk.DISABLED; self.play_button.config(state=play_save_state); self.save_button.config(state=play_save_state)
    def _start_generate_thread(self):
        api_key = self.api_key.get(); text = self.text_input.get("1.0", tk.END).strip(); voice = self.voice_var.get()
        if not api_key: messagebox.showerror("错误", "请输入 API Key。", parent=self); return
        if not text: messagebox.showerror("错误", "请输入要转换的文本。", parent=self); return
        if not voice: messagebox.showerror("错误", "请选择一个音色。", parent=self); return
        self._set_status("正在生成语音..."); self._toggle_buttons(False); self.audio_data = None
        thread = threading.Thread(target=self._generate_speech, args=(api_key, text), daemon=True); thread.start()
    def _generate_speech(self, api_key, text):
        model = self.model_var.get(); voice_name = self.voice_var.get(); full_voice_id = f"{model}:{voice_name}"
        speed = self.speed_var.get(); gain = self.gain_var.get(); response_format = self.format_var.get()
        payload = {"model": model, "input": text, "voice": full_voice_id, "response_format": response_format, "speed": speed, "gain": gain, "stream": False}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(TTS_API_URL, json=payload, headers=headers, timeout=60); response.raise_for_status()
            self.audio_data = response.content; self._set_status(f"语音生成成功！({len(self.audio_data)} bytes)")
        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try: error_detail = e.response.json(); error_message += f"\n错误详情: {error_detail}"
                except ValueError: error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message, parent=self); self._set_status("生成失败")
        except Exception as e: messagebox.showerror("错误", f"发生意外错误: {e}", parent=self); self._set_status("生成失败")
        finally: self.after(0, self._toggle_buttons, True)
    def _play_audio(self):
        if not self.audio_data: messagebox.showwarning("警告", "没有可播放的音频数据。", parent=self); return
        try:
            file_extension = self.format_var.get()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_audio_file: temp_audio_file.write(self.audio_data); temp_file_path = temp_audio_file.name
            self._set_status(f"正在尝试播放: {temp_file_path}")
            if os.name == 'nt': os.startfile(temp_file_path)
            elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin': subprocess.call(['open', temp_file_path])
            else: subprocess.call(['xdg-open', temp_file_path])
        except Exception as e: messagebox.showerror("播放错误", f"无法播放音频文件: {e}", parent=self); self._set_status("播放失败")
    def _save_audio(self):
        if not self.audio_data: messagebox.showwarning("警告", "没有可保存的音频数据。", parent=self); return
        file_extension = self.format_var.get()
        file_path = filedialog.asksaveasfilename(parent=self, defaultextension=f".{file_extension}", filetypes=[(f"{file_extension.upper()} 文件", f"*.{file_extension}"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, "wb") as f: f.write(self.audio_data)
                self._set_status(f"音频已保存到: {file_path}"); messagebox.showinfo("成功", f"音频文件已成功保存到\n{file_path}", parent=self)
            except Exception as e: messagebox.showerror("保存错误", f"无法保存文件: {e}", parent=self); self._set_status("保存失败")
        else: self._set_status("保存操作已取消")

# --- 语音转文本 (ASR) Frame 类 ---
class SpeechToTextFrame(ttk.Frame):
    def __init__(self, parent_notebook, main_app, initial_models):
        super().__init__(parent_notebook, width=800, height=700)
        self.pack_propagate(False); self.main_app = main_app; self.available_models = initial_models
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        default_model = DEFAULT_ASR_MODEL if DEFAULT_ASR_MODEL in self.available_models else (self.available_models if self.available_models else "")
        self.model_var = tk.StringVar(value=default_model); self.language_var = tk.StringVar(value=DEFAULT_ASR_LANGUAGE)
        self.file_path_var = tk.StringVar(value="尚未选择文件"); self.transcription_result = tk.StringVar(value="")
        self._create_widgets()
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        api_frame = ttk.LabelFrame(main_frame, text="API Key", padding="5"); api_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=60, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        file_params_frame = ttk.Frame(main_frame); file_params_frame.pack(fill=tk.X, pady=5)
        file_frame = ttk.LabelFrame(file_params_frame, text="选择音频文件", padding="5"); file_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="浏览...", command=self._select_file).pack(side=tk.LEFT, padx=5)
        ttk.Label(file_frame, textvariable=self.file_path_var, wraplength=300).pack(side=tk.LEFT, fill=tk.X, expand=True)
        params_frame = ttk.LabelFrame(file_params_frame, text="参数", padding="5"); params_frame.pack(side=tk.LEFT)
        lang_label = ttk.Label(params_frame, text="语言:"); lang_label.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        lang_menu = ttk.Combobox(params_frame, textvariable=self.language_var, values=ASR_LANGUAGES, state="readonly", width=5); lang_menu.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        model_label = ttk.Label(params_frame, text="模型:"); model_label.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.model_menu = ttk.Combobox(params_frame, textvariable=self.model_var, values=self.available_models, state="readonly", width=25); self.model_menu.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.transcribe_button = ttk.Button(main_frame, text="开始转录", command=self._start_transcribe_thread); self.transcribe_button.pack(pady=10)
        result_frame = ttk.LabelFrame(main_frame, text="转录结果", padding="5"); result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=15, state=tk.DISABLED); self.result_text.pack(fill=tk.BOTH, expand=True)
    def _select_file(self):
        filetypes = [("音频文件", "*.wav *.mp3 *.m4a *.ogg *.flac"), ("所有文件", "*.*")]
        filepath = filedialog.askopenfilename(parent=self, title="选择要转录的音频文件", filetypes=filetypes)
        if filepath: self.file_path_var.set(filepath); self._set_status(f"已选择文件: {os.path.basename(filepath)}")
        else: self._set_status("文件选择已取消")
    def _set_status(self, message): self.main_app.set_status(message)
    def _start_transcribe_thread(self):
        api_key = self.api_key.get(); file_path = self.file_path_var.get(); language = self.language_var.get(); model = self.model_var.get()
        if not api_key: messagebox.showerror("错误", "请输入 API Key。", parent=self); return
        if not file_path or file_path == "尚未选择文件": messagebox.showerror("错误", "请选择要转录的音频文件。", parent=self); return
        if not os.path.exists(file_path): messagebox.showerror("错误", f"文件不存在: {file_path}", parent=self); return
        if not language: messagebox.showerror("错误", "请选择语言。", parent=self); return
        if not model: messagebox.showerror("错误", "请选择模型。", parent=self); return
        self._set_status("正在上传并转录音频..."); self.transcribe_button.config(state=tk.DISABLED)
        self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END); self.result_text.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._transcribe_audio, args=(api_key, file_path, language, model), daemon=True); thread.start()
    def _transcribe_audio(self, api_key, file_path, language, model):
        headers = {"Authorization": f"Bearer {api_key}"}
        audio_file = None
        try:
            audio_file = open(file_path, 'rb')
            files = {'file': audio_file}
            data = {'model': model, 'language': language}
            response = requests.post(ASR_API_URL, headers=headers, files=files, data=data, timeout=180)
            response.raise_for_status()
            result = response.json()
            print("--- DEBUG: Full ASR API Response ---"); print(result); print("--- END DEBUG ---")
            transcribed_text = result.get('text', '未能获取转录文本')
            self.after(0, self._display_transcription, transcribed_text)
            self._set_status("语音转录成功！")
        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try: error_detail = e.response.json(); error_message += f"\n错误详情: {error_detail}"
                except ValueError: error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message, parent=self); self._set_status("转录失败")
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误: {e}", parent=self); self._set_status("转录失败")
        finally:
            if audio_file and not audio_file.closed:
                audio_file.close()
                print(f"--- DEBUG: Audio file closed in finally block. ---")
            self.after(0, lambda: self.transcribe_button.config(state=tk.NORMAL))
    def _display_transcription(self, text):
        self.result_text.config(state=tk.NORMAL); self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, text); self.result_text.config(state=tk.DISABLED)
    def update_model_list(self, new_models):
        self.available_models = new_models; current_selection = self.model_var.get(); self.model_menu['values'] = self.available_models
        if self.available_models: self.model_var.set(self.available_models if current_selection not in self.available_models else current_selection)
        else: self.model_var.set("")

# --- 模型检测器 Frame 类 ---
class ModelCheckerFrame(ttk.Frame):
    def __init__(self, parent_notebook, main_app):
        super().__init__(parent_notebook, width=800, height=700); self.pack_propagate(False); self.main_app = main_app
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY); self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []
        self._create_widgets()
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        top_frame = ttk.Frame(main_frame); top_frame.pack(fill=tk.X, pady=5)
        api_frame = ttk.LabelFrame(top_frame, text="API Key", padding="5"); api_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Entry(api_frame, textvariable=self.api_key, width=45, show="*").pack(fill=tk.X)
        button_frame = ttk.Frame(top_frame); button_frame.pack(side=tk.LEFT)
        check_button = ttk.Button(button_frame, text="检测可用模型", command=self._start_check_thread); check_button.pack(side=tk.TOP, pady=(0, 5))
        self.update_button = ttk.Button(button_frame, text="更新其他选项卡列表", command=self._update_other_tabs_models, state=tk.DISABLED); self.update_button.pack(side=tk.TOP)
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL); paned_window.pack(fill=tk.BOTH, expand=True, pady=5)
        image_result_frame = ttk.LabelFrame(paned_window, text="可用文生图模型列表", padding="5", height=200); image_result_frame.pack_propagate(False); paned_window.add(image_result_frame, weight=1)
        self.image_result_text = scrolledtext.ScrolledText(image_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.image_result_text.pack(fill=tk.BOTH, expand=True)
        tts_result_frame = ttk.LabelFrame(paned_window, text="可用文本转语音 (TTS) 模型列表", padding="5", height=200); tts_result_frame.pack_propagate(False); paned_window.add(tts_result_frame, weight=1)
        self.tts_result_text = scrolledtext.ScrolledText(tts_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.tts_result_text.pack(fill=tk.BOTH, expand=True)
        asr_result_frame = ttk.LabelFrame(paned_window, text="可用语音转文本 (ASR) 模型列表", padding="5", height=200); asr_result_frame.pack_propagate(False); paned_window.add(asr_result_frame, weight=1)
        self.asr_result_text = scrolledtext.ScrolledText(asr_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.asr_result_text.pack(fill=tk.BOTH, expand=True)
    def _set_status(self, message): self.main_app.set_status(message)
    def _start_check_thread(self):
        api_key = self.api_key.get();
        if not api_key: messagebox.showerror("错误", "请输入 API Key。", parent=self); return
        self._set_status("正在检测模型..."); self.update_button.config(state=tk.DISABLED)
        for text_widget in [self.image_result_text, self.tts_result_text, self.asr_result_text]: text_widget.config(state=tk.NORMAL); text_widget.delete('1.0', tk.END); text_widget.config(state=tk.DISABLED)
        self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []
        thread = threading.Thread(target=self._check_models, args=(api_key,), daemon=True); thread.start()
    def _check_models(self, api_key):
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(MODELS_LIST_API_URL, headers=headers, timeout=30); response.raise_for_status()
            models_data = response.json(); print("--- DEBUG: Full Models API Response ---"); print(models_data); print("--- END DEBUG ---")
            self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []
            if 'data' in models_data and isinstance(models_data['data'], list):
                for model_info in models_data['data']:
                    model_id = model_info.get('id', '').lower(); model_id_original = model_info.get('id', '未知ID')
                    if 'stable-diffusion' in model_id or 'sdxl' in model_id or 'flux' in model_id or 'kolors' in model_id or 'image' in model_id or 'sd3' in model_id: self.detected_image_models.append(model_id_original)
                    elif 'audio' in model_id or 'speech' in model_id or 'tts' in model_id or 'cosyvoice' in model_id or 'fish' in model_id: self.detected_tts_models.append(model_id_original)
                    elif 'sensevoice' in model_id or 'asr' in model_id or 'transcription' in model_id: self.detected_asr_models.append(model_id_original)
            status_msg = []
            if self.detected_image_models: status_msg.append(f"检测到 {len(self.detected_image_models)} 个文生图")
            if self.detected_tts_models: status_msg.append(f"检测到 {len(self.detected_tts_models)} 个 TTS")
            if self.detected_asr_models: status_msg.append(f"检测到 {len(self.detected_asr_models)} 个 ASR")
            final_status = "，".join(status_msg) + " 模型。" if status_msg else "未检测到相关模型或 API 返回格式不符。"
            if not status_msg: messagebox.showwarning("未找到模型", "未能识别出文生图、TTS 或 ASR 模型。\n请检查 API Key 或控制台输出。", parent=self)
            self._set_status(final_status)
            if self.detected_image_models or self.detected_tts_models or self.detected_asr_models: self.after(0, lambda: self.update_button.config(state=tk.NORMAL))
            self.after(0, self._display_models)
        except requests.exceptions.RequestException as e:
            error_message = f"API 请求失败: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try: error_detail = e.response.json(); error_message += f"\n错误详情: {error_detail}"
                except ValueError: error_message += f"\n服务器响应: {e.response.text}"
            messagebox.showerror("API 错误", error_message, parent=self); self._set_status("检测失败")
        except Exception as e: messagebox.showerror("错误", f"发生意外错误: {e}", parent=self); self._set_status("检测失败")
    def _display_models(self):
        self.image_result_text.config(state=tk.NORMAL); self.image_result_text.delete('1.0', tk.END); self.image_result_text.insert(tk.END, "\n".join(self.detected_image_models) if self.detected_image_models else "未找到可用的文生图模型。"); self.image_result_text.config(state=tk.DISABLED)
        self.tts_result_text.config(state=tk.NORMAL); self.tts_result_text.delete('1.0', tk.END); self.tts_result_text.insert(tk.END, "\n".join(self.detected_tts_models) if self.detected_tts_models else "未找到可用的文本转语音模型。"); self.tts_result_text.config(state=tk.DISABLED)
        self.asr_result_text.config(state=tk.NORMAL); self.asr_result_text.delete('1.0', tk.END); self.asr_result_text.insert(tk.END, "\n".join(self.detected_asr_models) if self.detected_asr_models else "未找到可用的语音转文本模型。"); self.asr_result_text.config(state=tk.DISABLED)
    def _update_other_tabs_models(self):
        if not self.detected_image_models and not self.detected_tts_models and not self.detected_asr_models: messagebox.showinfo("无模型", "没有检测到可更新的模型列表。", parent=self); return
        updated_image, updated_tts, updated_asr = False, False, False
        if self.detected_image_models:
            try: self.main_app.image_gen_frame.update_model_list(self.detected_image_models); updated_image = True
            except Exception as e: messagebox.showerror("更新错误", f"更新文生图模型列表时出错: {e}", parent=self)
        if self.detected_tts_models:
             try: self.main_app.tts_frame.update_model_list(self.detected_tts_models); updated_tts = True
             except Exception as e: messagebox.showerror("更新错误", f"更新 TTS 模型列表时出错: {e}", parent=self)
        if self.detected_asr_models:
             try: self.main_app.stt_frame.update_model_list(self.detected_asr_models); updated_asr = True
             except Exception as e: messagebox.showerror("更新错误", f"更新 ASR 模型列表时出错: {e}", parent=self)
        if updated_image or updated_tts or updated_asr:
            update_msg = []
            if updated_image: update_msg.append("文生图")
            if updated_tts: update_msg.append("TTS")
            if updated_asr: update_msg.append("ASR")
            messagebox.showinfo("更新成功", f"{'、'.join(update_msg)} 模型列表已更新！\n请切换到对应选项卡查看。", parent=self); self._set_status("模型列表已更新到其他选项卡。")
        else: self._set_status("模型列表更新失败。")

# --- 启动应用 ---
if __name__ == "__main__":
    app = SiliconFlowSuiteApp()
    app.mainloop()