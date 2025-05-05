import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import threading
import os
import tempfile
import subprocess
import json
import re
from PIL import Image, ImageTk, UnidentifiedImageError
import io
import base64 # 确保导入 base64

# --- 全局配置 ---
DEFAULT_API_KEY = "sk-leirgmdw"
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

# --- 文本聊天配置 ---
CHAT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
INITIAL_CHAT_MODELS = sorted(list(set([ # Use set to remove duplicates and sort (保持之前的更新)
   "THUDM/chatglm3-6b",
   "THUDM/glm-4-9b-chat",
   "Qwen/Qwen2-7B-Instruct",
   "Qwen/Qwen2-1.5B-Instruct",
   "internlm/internlm2_5-7b-chat",
   "Pro/Qwen/Qwen2-7B-Instruct",
   "Pro/Qwen/Qwen2-1.5B-Instruct",
   "Pro/THUDM/glm-4-9b-chat",
   "internlm/internlm2_5-20b-chat",
   "deepseek-ai/DeepSeek-V2.5",
   "Qwen/Qwen2.5-72B-Instruct",
   "Qwen/Qwen2.5-7B-Instruct",
   "Qwen/Qwen2.5-14B-Instruct",
   "Qwen/Qwen2.5-32B-Instruct",
   "Qwen/Qwen2.5-Coder-7B-Instruct",
   "Pro/Qwen/Qwen2.5-7B-Instruct",
   "Qwen/Qwen2.5-72B-Instruct-128K",
   "Qwen/Qwen2-VL-72B-Instruct", # Vision Model
   "Pro/Qwen/Qwen2-VL-7B-Instruct", # Vision Model
   "LoRA/Qwen/Qwen2.5-7B-Instruct",
   "Pro/Qwen/Qwen2.5-Coder-7B-Instruct",
   "LoRA/Qwen/Qwen2.5-72B-Instruct",
   "Qwen/Qwen2.5-Coder-32B-Instruct",
   "Qwen/QwQ-32B-Preview",
   "LoRA/Qwen/Qwen2.5-14B-Instruct",
   "LoRA/Qwen/Qwen2.5-32B-Instruct",
   "deepseek-ai/deepseek-vl2", # Vision Model
   "Qwen/QVQ-72B-Preview",
   "Qwen/Qwen2.5-VL-72B-Instruct", # Vision Model
   "Pro/Qwen/Qwen2.5-VL-7B-Instruct", # Vision Model
   "deepseek-ai/DeepSeek-V3",
   "deepseek-ai/DeepSeek-R1", # Reasoning Model
   "Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", # Reasoning Model
   "Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", # Reasoning Model
   "Pro/deepseek-ai/DeepSeek-R1-Distill-Llama-8B", # Reasoning Model
   "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B", # Reasoning Model
   "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", # Reasoning Model
   "deepseek-ai/DeepSeek-R1-Distill-Llama-70B", # Reasoning Model
   "Pro/deepseek-ai/DeepSeek-R1", # Reasoning Model
   "Pro/deepseek-ai/DeepSeek-V3",
   "Qwen/QwQ-32B",
   "Pro/deepseek-ai/DeepSeek-V3-1226",
   "Qwen/Qwen2.5-VL-32B-Instruct", # Vision Model
   "THUDM/GLM-Z1-32B-0414", # Reasoning Model?
   "THUDM/GLM-4-32B-0414",
   "THUDM/GLM-Z1-9B-0414", # Reasoning Model?
   "THUDM/GLM-4-9B-0414",
   "THUDM/GLM-Z1-Rumination-32B-0414", # Reasoning Model
   "Qwen/Qwen3-8B",
   "Qwen/Qwen3-14B",
   "Qwen/Qwen3-32B",
   "Qwen/Qwen3-30B-A3B",
   "Qwen/Qwen3-235B-A22B",
   "meta-llama/Meta-Llama-3.1-8B-Instruct",
   "meta-llama/Meta-Llama-3.1-70B-Instruct",
   "meta-llama/Meta-Llama-3.1-405B-Instruct",
   "mistralai/Mixtral-8x7B-Instruct-v0.1",
   "mistralai/Mistral-7B-Instruct-v0.3",
   "01-ai/Yi-1.5-9B-Chat",
   "01-ai/Yi-1.5-34B-Chat",
   "google/gemma-2-9b-it",
   "google/gemma-2-27b-it",
   "OpenGVLab/InternVL2-26B", # Vision Model
   "Pro/OpenGVLab/InternVL2-8B", # Vision Model
])))
DEFAULT_CHAT_MODEL = "THUDM/glm-4-9b-chat"


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
        self.chat_frame = ChatFrame(self.notebook, self, INITIAL_CHAT_MODELS) # 添加 ChatFrame 实例

        self.notebook.add(self.image_gen_frame, text='文生图')
        self.notebook.add(self.tts_frame, text='文本转语音 (TTS)')
        self.notebook.add(self.stt_frame, text='语音转文本 (ASR)')
        self.notebook.add(self.chat_frame, text='文本聊天') # 调整顺序：添加 ChatFrame 到 Notebook
        self.notebook.add(self.model_checker_frame, text='模型检测器') # 模型检测器放在最后

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
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY); self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []; self.detected_chat_models = [] # 添加聊天模型列表
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
        image_result_frame = ttk.LabelFrame(paned_window, text="可用文生图模型列表", padding="5", height=150); image_result_frame.pack_propagate(False); paned_window.add(image_result_frame, weight=1) # 调整高度
        self.image_result_text = scrolledtext.ScrolledText(image_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.image_result_text.pack(fill=tk.BOTH, expand=True)
        tts_result_frame = ttk.LabelFrame(paned_window, text="可用文本转语音 (TTS) 模型列表", padding="5", height=150); tts_result_frame.pack_propagate(False); paned_window.add(tts_result_frame, weight=1) # 调整高度
        self.tts_result_text = scrolledtext.ScrolledText(tts_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.tts_result_text.pack(fill=tk.BOTH, expand=True)
        asr_result_frame = ttk.LabelFrame(paned_window, text="可用语音转文本 (ASR) 模型列表", padding="5", height=150); asr_result_frame.pack_propagate(False); paned_window.add(asr_result_frame, weight=1) # 调整高度
        self.asr_result_text = scrolledtext.ScrolledText(asr_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.asr_result_text.pack(fill=tk.BOTH, expand=True)
        chat_result_frame = ttk.LabelFrame(paned_window, text="可用文本聊天模型列表", padding="5", height=150); chat_result_frame.pack_propagate(False); paned_window.add(chat_result_frame, weight=1) # 添加聊天模型显示区域
        self.chat_result_text = scrolledtext.ScrolledText(chat_result_frame, wrap=tk.WORD, state=tk.DISABLED); self.chat_result_text.pack(fill=tk.BOTH, expand=True)

    def _set_status(self, message): self.main_app.set_status(message)
    def _start_check_thread(self):
        api_key = self.api_key.get();
        if not api_key: messagebox.showerror("错误", "请输入 API Key。", parent=self); return
        self._set_status("正在检测模型..."); self.update_button.config(state=tk.DISABLED)
        # 清空所有结果区域
        for text_widget in [self.image_result_text, self.tts_result_text, self.asr_result_text, self.chat_result_text]:
            text_widget.config(state=tk.NORMAL); text_widget.delete('1.0', tk.END); text_widget.config(state=tk.DISABLED)
        # 重置所有检测到的模型列表
        self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []; self.detected_chat_models = []
        thread = threading.Thread(target=self._check_models, args=(api_key,), daemon=True); thread.start()
    def _check_models(self, api_key):
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(MODELS_LIST_API_URL, headers=headers, timeout=30); response.raise_for_status()
            models_data = response.json(); print("--- DEBUG: Full Models API Response ---"); print(models_data); print("--- END DEBUG ---")
            self.detected_image_models = []; self.detected_tts_models = []; self.detected_asr_models = []; self.detected_chat_models = [] # 重置列表
            # 更新关键词列表以包含新模型类型 (保持之前的更新, 确保 vision/reasoning 关键词在 chat_keywords 中)
            chat_keywords = ["chat", "instruct", "llama", "qwen", "deepseek", "mistral", "mixtral", "gemma", "glm", "yi", "chatglm", "internlm", "coder", "vl", "preview", "distill", "rumination", "glm-z1", "qwen3", "v2.5", "v3", "qwq", "qvq", "-r1", "-z1", "-a3b", "-a22b", "vision", "reasoning", "internvl"] # 添加 vision/reasoning/internvl
            image_keywords = ['stable-diffusion', 'sdxl', 'flux', 'kolors', 'image', 'sd3']
            tts_keywords = ['audio', 'speech', 'tts', 'cosyvoice', 'fish', 'sovits']
            asr_keywords = ['sensevoice', 'asr', 'transcription']
            # 明确排除 embedding/reranker 模型
            exclude_keywords = ['embed', 'bge-', 'bce-', 'reranker']

            if 'data' in models_data and isinstance(models_data['data'], list):
                for model_info in models_data['data']:
                    model_id = model_info.get('id', '').lower(); model_id_original = model_info.get('id', '未知ID')
                    # 改进分类逻辑：先排除，再按优先级分类
                    if any(keyword in model_id for keyword in exclude_keywords):
                        continue # 跳过 embedding/reranker 模型

                    is_classified = False
                    # 1. 图像模型
                    if any(keyword in model_id for keyword in image_keywords):
                        self.detected_image_models.append(model_id_original); is_classified = True
                    # 2. TTS 模型 (排除包含聊天/视觉关键词的模型)
                    if not is_classified and any(keyword in model_id for keyword in tts_keywords) and not any(chat_kw in model_id for chat_kw in ["vl", "chat", "instruct"]):
                        self.detected_tts_models.append(model_id_original); is_classified = True
                    # 3. ASR 模型
                    if not is_classified and any(keyword in model_id for keyword in asr_keywords):
                        self.detected_asr_models.append(model_id_original); is_classified = True
                    # 4. 聊天模型 (包含所有剩余的含聊天/视觉/推理关键词的模型)
                    if not is_classified and any(keyword in model_id for keyword in chat_keywords):
                        self.detected_chat_models.append(model_id_original); is_classified = True
                    # 5. 捕获其他未分类的模型
                    elif not is_classified:
                       print(f"--- DEBUG: Unclassified model: {model_id_original}")


            # 去重并排序
            self.detected_image_models = sorted(list(set(self.detected_image_models)))
            self.detected_tts_models = sorted(list(set(self.detected_tts_models)))
            self.detected_asr_models = sorted(list(set(self.detected_asr_models)))
            self.detected_chat_models = sorted(list(set(self.detected_chat_models)))

            status_msg = []
            if self.detected_image_models: status_msg.append(f"检测到 {len(self.detected_image_models)} 个文生图")
            if self.detected_tts_models: status_msg.append(f"检测到 {len(self.detected_tts_models)} 个 TTS")
            if self.detected_asr_models: status_msg.append(f"检测到 {len(self.detected_asr_models)} 个 ASR")
            if self.detected_chat_models: status_msg.append(f"检测到 {len(self.detected_chat_models)} 个聊天") # 添加聊天模型计数
            final_status = "，".join(status_msg) + " 模型。" if status_msg else "未检测到相关模型或 API 返回格式不符。"
            if not status_msg: messagebox.showwarning("未找到模型", "未能识别出文生图、TTS、ASR 或聊天模型。\n请检查 API Key 或控制台输出。", parent=self)
            self._set_status(final_status)
            # 只要检测到任何一种模型，就启用更新按钮
            if self.detected_image_models or self.detected_tts_models or self.detected_asr_models or self.detected_chat_models:
                self.after(0, lambda: self.update_button.config(state=tk.NORMAL))
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
        # 显示聊天模型
        self.chat_result_text.config(state=tk.NORMAL); self.chat_result_text.delete('1.0', tk.END); self.chat_result_text.insert(tk.END, "\n".join(self.detected_chat_models) if self.detected_chat_models else "未找到可用的聊天模型。"); self.chat_result_text.config(state=tk.DISABLED)

    def _update_other_tabs_models(self):
        # 检查是否有任何模型被检测到
        if not any([self.detected_image_models, self.detected_tts_models, self.detected_asr_models, self.detected_chat_models]):
            messagebox.showinfo("无模型", "没有检测到可更新的模型列表。", parent=self); return

        updated_tabs = [] # 用于记录哪些选项卡被更新了
        # 更新文生图
        if self.detected_image_models:
            try: self.main_app.image_gen_frame.update_model_list(self.detected_image_models); updated_tabs.append("文生图")
            except Exception as e: messagebox.showerror("更新错误", f"更新文生图模型列表时出错: {e}", parent=self)
        # 更新 TTS
        if self.detected_tts_models:
             try: self.main_app.tts_frame.update_model_list(self.detected_tts_models); updated_tabs.append("TTS")
             except Exception as e: messagebox.showerror("更新错误", f"更新 TTS 模型列表时出错: {e}", parent=self)
        # 更新 ASR
        if self.detected_asr_models:
             try: self.main_app.stt_frame.update_model_list(self.detected_asr_models); updated_tabs.append("ASR")
             except Exception as e: messagebox.showerror("更新错误", f"更新 ASR 模型列表时出错: {e}", parent=self)
        # 更新聊天
        if self.detected_chat_models:
             try: self.main_app.chat_frame.update_model_list(self.detected_chat_models); updated_tabs.append("聊天")
             except Exception as e: messagebox.showerror("更新错误", f"更新聊天模型列表时出错: {e}", parent=self)

        if updated_tabs:
            messagebox.showinfo("更新成功", f"{'、'.join(updated_tabs)} 模型列表已更新！\n请切换到对应选项卡查看。", parent=self); self._set_status("模型列表已更新到其他选项卡。")
        else: self._set_status("模型列表更新失败。")

# --- 文本聊天 Frame 类 ---
class ChatFrame(ttk.Frame):
   def __init__(self, parent_notebook, main_app, initial_models):
       super().__init__(parent_notebook, width=800, height=700)
       self.pack_propagate(False)
       self.main_app = main_app
       self.available_models = initial_models
       self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
       default_model = DEFAULT_CHAT_MODEL if DEFAULT_CHAT_MODEL in self.available_models else (self.available_models[0] if self.available_models else "")
       self.model_var = tk.StringVar(value=default_model)
       self.conversation_history = [] # 存储对话历史 (不含 System Prompt)
       self.current_response_content = "" # 用于流式输出累积
       self.current_response_role = "assistant" # 用于流式输出角色

       # --- Add variables for new parameters ---
       self.temperature_var = tk.DoubleVar(value=0.7)
       self.top_p_var = tk.DoubleVar(value=0.9)
       self.max_tokens_var = tk.IntVar(value=2048)
       self.presence_penalty_var = tk.DoubleVar(value=0.0)
       self.frequency_penalty_var = tk.DoubleVar(value=0.0)
       self.stop_var = tk.StringVar(value="")
       self.image_url_var = tk.StringVar(value="") # For vision models URL input
       self.image_path_var = tk.StringVar(value="") # For local image path
       self.image_detail_var = tk.StringVar(value="high") # Add variable for image detail

       self._create_widgets()

   def _create_widgets(self):
       # Use PanedWindow for better layout control
       paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
       paned_window.pack(fill=tk.BOTH, expand=True)

       # --- Top Control Frame ---
       top_control_frame = ttk.Frame(paned_window, padding="5")
       paned_window.add(top_control_frame, weight=0) # Don't expand vertically initially

       # API Key and Model Selection (side by side)
       api_model_frame = ttk.Frame(top_control_frame)
       api_model_frame.pack(fill=tk.X, pady=(0, 5))

       api_frame = ttk.LabelFrame(api_model_frame, text="API Key", padding="5")
       api_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
       ttk.Entry(api_frame, textvariable=self.api_key, width=40, show="*").pack(fill=tk.X)

       model_frame = ttk.LabelFrame(api_model_frame, text="选择模型", padding="5")
       model_frame.pack(side=tk.LEFT, padx=(0, 5))
       self.model_menu = ttk.Combobox(model_frame, textvariable=self.model_var, values=self.available_models, state="readonly", width=35)
       self.model_menu.pack()

       # --- System Prompt Frame ---
       system_prompt_frame = ttk.LabelFrame(top_control_frame, text="System Prompt (AI 角色/指令)", padding="5")
       system_prompt_frame.pack(fill=tk.X, pady=5)
       self.system_prompt_input = scrolledtext.ScrolledText(system_prompt_frame, wrap=tk.WORD, height=3, width=70)
       self.system_prompt_input.pack(fill=tk.X, expand=True)

       # --- Image Input Frame ---
       image_input_frame = ttk.LabelFrame(top_control_frame, text="图像输入 (可选, Vision 模型)", padding="5")
       image_input_frame.pack(fill=tk.X, pady=5)
       ttk.Button(image_input_frame, text="浏览本地图片...", command=self._select_image_file).pack(side=tk.LEFT, padx=(0, 5))
       self.image_path_label = ttk.Label(image_input_frame, text="未选择本地图片", anchor=tk.W, relief=tk.GROOVE, width=40) # Use Label to display path
       self.image_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
       ttk.Label(image_input_frame, text="或输入 URL:").pack(side=tk.LEFT, padx=(10, 5))
       image_url_entry = ttk.Entry(image_input_frame, textvariable=self.image_url_var, width=30)
       image_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)


       # --- Parameters Frame ---
       params_frame = ttk.LabelFrame(top_control_frame, text="参数设置", padding="10")
       params_frame.pack(fill=tk.X, pady=5)

       # Grid layout for parameters
       params_frame.columnconfigure(1, weight=1) # Allow entry/scale to expand
       params_frame.columnconfigure(4, weight=1) # Allow entry/scale to expand for right column
       params_frame.columnconfigure(7, weight=1) # Allow entry/scale to expand for third column

       ttk.Label(params_frame, text="Temperature:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
       temp_scale = ttk.Scale(params_frame, from_=0.0, to=2.0, variable=self.temperature_var, orient=tk.HORIZONTAL, length=80)
       temp_scale.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
       ttk.Label(params_frame, textvariable=self.temperature_var).grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)

       ttk.Label(params_frame, text="Top P:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
       top_p_scale = ttk.Scale(params_frame, from_=0.0, to=1.0, variable=self.top_p_var, orient=tk.HORIZONTAL, length=80)
       top_p_scale.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
       ttk.Label(params_frame, textvariable=self.top_p_var).grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)

       ttk.Label(params_frame, text="Max Tokens:").grid(row=0, column=3, padx=(15, 5), pady=2, sticky=tk.W)
       max_tokens_spinbox = ttk.Spinbox(params_frame, from_=1, to=16384, increment=64, textvariable=self.max_tokens_var, width=7)
       max_tokens_spinbox.grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)

       ttk.Label(params_frame, text="Stop Sequences:").grid(row=1, column=3, padx=(15, 5), pady=2, sticky=tk.W)
       stop_entry = ttk.Entry(params_frame, textvariable=self.stop_var, width=10)
       stop_entry.grid(row=1, column=4, padx=5, pady=2, sticky=tk.W)
       ttk.Label(params_frame, text="(,)").grid(row=1, column=5, padx=0, pady=2, sticky=tk.W)


       ttk.Label(params_frame, text="Presence Penalty:").grid(row=0, column=6, padx=(15, 5), pady=2, sticky=tk.W)
       presence_scale = ttk.Scale(params_frame, from_=-2.0, to=2.0, variable=self.presence_penalty_var, orient=tk.HORIZONTAL, length=80)
       presence_scale.grid(row=0, column=7, padx=5, pady=2, sticky=tk.EW)
       ttk.Label(params_frame, textvariable=self.presence_penalty_var).grid(row=0, column=8, padx=5, pady=2, sticky=tk.W)

       ttk.Label(params_frame, text="Frequency Penalty:").grid(row=1, column=6, padx=(15, 5), pady=2, sticky=tk.W)
       frequency_scale = ttk.Scale(params_frame, from_=-2.0, to=2.0, variable=self.frequency_penalty_var, orient=tk.HORIZONTAL, length=80)
       frequency_scale.grid(row=1, column=7, padx=5, pady=2, sticky=tk.EW)
       ttk.Label(params_frame, textvariable=self.frequency_penalty_var).grid(row=1, column=8, padx=5, pady=2, sticky=tk.W)

       # Image Detail (for Vision models) - Moved to Image Input Frame
       ttk.Label(params_frame, text="Image Detail:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
       image_detail_menu = ttk.Combobox(params_frame, textvariable=self.image_detail_var, values=["auto", "low", "high"], state="readonly", width=8)
       image_detail_menu.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)


       # --- Chat History Display Area ---
       chat_display_frame = ttk.LabelFrame(paned_window, text="聊天记录", padding="5")
       paned_window.add(chat_display_frame, weight=1) # Allow chat history to expand

       self.chat_display = scrolledtext.ScrolledText(chat_display_frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
       self.chat_display.pack(fill=tk.BOTH, expand=True)
       # Configure tags for different roles
       self.chat_display.tag_configure("user", foreground="blue")
       self.chat_display.tag_configure("assistant", foreground="green")
       self.chat_display.tag_configure("system", foreground="gray", font=("TkDefaultFont", 9, "italic"))
       self.chat_display.tag_configure("error", foreground="red")

       # --- Input Area ---
       input_frame = ttk.Frame(paned_window, padding="5")
       paned_window.add(input_frame, weight=0) # Don't expand vertically

       self.input_entry = ttk.Entry(input_frame, width=70)
       self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
       self.input_entry.bind("<Return>", self._start_send_thread) # Bind Enter key

       self.send_button = ttk.Button(input_frame, text="发送", command=self._start_send_thread)
       self.send_button.pack(side=tk.LEFT)

       self.clear_button = ttk.Button(input_frame, text="清空记录", command=self._clear_history)
       self.clear_button.pack(side=tk.LEFT, padx=(5, 0))

   def update_model_list(self, new_models):
       self.available_models = new_models
       current_selection = self.model_var.get()
       self.model_menu['values'] = self.available_models
       # Try to keep the current selection if it's still valid, otherwise pick the first available
       if self.available_models:
           if current_selection in self.available_models:
               self.model_var.set(current_selection)
           else:
               self.model_var.set(self.available_models[0])
       else:
           self.model_var.set("")

   def _set_status(self, message):
       self.main_app.set_status(message)

   def _toggle_controls(self, enable):
       state = tk.NORMAL if enable else tk.DISABLED
       self.send_button.config(state=state)
       self.input_entry.config(state=state)
       self.clear_button.config(state=state)
       # Also disable/enable parameter controls? Maybe not, allow changing params even while waiting
       # self.model_menu.config(state=tk.NORMAL if enable else tk.DISABLED)
       # self.system_prompt_input.config(state=state) # Keep system prompt editable

   def _display_message(self, role, content, tag=None):
       """Displays a complete message in the chat window."""
       self.chat_display.config(state=tk.NORMAL)
       if tag is None:
           tag = role # Default tag is the role itself
       prefix = ""
       if role == "user":
           prefix = "You: "
       elif role == "assistant":
           prefix = "AI: "
       elif role == "system":
           prefix = "System: "
       elif role == "error":
           prefix = "Error: "

       self.chat_display.insert(tk.END, f"{prefix}{content}\n\n", tag)
       self.chat_display.config(state=tk.DISABLED)
       self.chat_display.see(tk.END) # Scroll to the bottom

   def _display_stream_start(self, role="assistant"):
        """Displays the prefix for a streaming message."""
        self.chat_display.config(state=tk.NORMAL)
        prefix = "AI: " if role == "assistant" else "System: " # Assuming reasoning is system
        self.chat_display.insert(tk.END, prefix, role) # Use role as tag
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

   def _append_message_chunk(self, chunk_text, role="assistant"):
        """Appends a chunk of text to the chat display during streaming."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, chunk_text, role) # Use role as tag
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

   def _display_stream_end(self):
        """Adds the final newline after a stream is complete."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)


   def _clear_history(self):
       if messagebox.askyesno("确认", "确定要清空聊天记录和设定吗？", parent=self):
           self.conversation_history = []
           self.chat_display.config(state=tk.NORMAL)
           self.chat_display.delete('1.0', tk.END)
           self.chat_display.config(state=tk.DISABLED)
           self.system_prompt_input.delete('1.0', tk.END) # Clear system prompt
           self.image_path_var.set("") # Clear image path
           self.image_path_label.config(text="未选择本地图片")
           self.image_url_var.set("") # Clear image url
           self._set_status("聊天记录和设定已清空")

   def _select_image_file(self):
        """Opens a file dialog to select a local image."""
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.webp *.gif"), ("All files", "*.*")]
        filepath = filedialog.askopenfilename(parent=self, title="选择本地图片文件", filetypes=filetypes)
        if filepath:
            self.image_path_var.set(filepath)
            self.image_path_label.config(text=os.path.basename(filepath)) # Show filename in label
            self.image_url_var.set("") # Clear URL if local file is chosen
            self._set_status(f"已选择本地图片: {os.path.basename(filepath)}")
        else:
            # Keep existing path if dialog is cancelled
            # self.image_path_var.set("")
            # self.image_path_label.config(text="未选择本地图片")
            self._set_status("图片选择已取消")

   def _image_to_base64(self, image_path):
        """Converts an image file to a Base64 encoded WEBP string."""
        try:
            with Image.open(image_path) as img:
                # Ensure image is in RGB mode for WEBP saving
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                byte_arr = io.BytesIO()
                # Save as WEBP for potentially smaller size, adjust quality if needed
                img.save(byte_arr, format='WEBP', quality=85)
                byte_arr = byte_arr.getvalue()
                base64_str = base64.b64encode(byte_arr).decode('utf-8')
                # Return the data URI scheme
                return f"data:image/webp;base64,{base64_str}"
        except FileNotFoundError:
            messagebox.showerror("错误", f"图片文件未找到: {image_path}", parent=self)
            return None
        except UnidentifiedImageError:
             messagebox.showerror("错误", f"无法识别的图片格式: {image_path}", parent=self)
             return None
        except Exception as e:
            messagebox.showerror("图片转换错误", f"转换图片时出错: {e}", parent=self)
            return None

   def _start_send_thread(self, event=None): # Accept event argument for Enter key binding
       api_key = self.api_key.get()
       model = self.model_var.get()
       user_input = self.input_entry.get().strip()
       system_prompt = self.system_prompt_input.get("1.0", tk.END).strip() # Get system prompt
       image_path = self.image_path_var.get() # Get local image path

       if not api_key:
           messagebox.showerror("错误", "请输入 API Key。", parent=self)
           return
       if not model:
           messagebox.showerror("错误", "请选择一个模型。", parent=self)
           return
       if not user_input:
           # Allow sending just an image with a default prompt if needed, or show warning
           # For now, require text input
           messagebox.showwarning("警告", "请输入消息内容。", parent=self)
           return

       self._set_status("正在发送消息...")
       self._toggle_controls(False)

       # Display user message immediately
       self._display_message("user", user_input) # Display complete user message

       # Add user message to history (simple text for now, complex content added in _send_chat_request)
       self.conversation_history.append({"role": "user", "content": user_input})

       self.input_entry.delete(0, tk.END) # Clear input field

       # Pass system_prompt and image_path to the thread
       thread = threading.Thread(target=self._send_chat_request, args=(api_key, model, system_prompt, image_path), daemon=True)
       thread.start()

   def _send_chat_request(self, api_key, model, system_prompt, image_path):
       # --- Retrieve parameters ---
       temperature = self.temperature_var.get()
       top_p = self.top_p_var.get()
       try:
           max_tokens = self.max_tokens_var.get()
           if max_tokens <= 0: max_tokens = None # Treat 0 or less as None (API default)
       except tk.TclError:
           max_tokens = None # Handle invalid input
       presence_penalty = self.presence_penalty_var.get()
       frequency_penalty = self.frequency_penalty_var.get()
       stop_sequences = [s.strip() for s in self.stop_var.get().split(',') if s.strip()]
       image_url_from_input = self.image_url_var.get().strip() # Get image URL from input field
       image_detail = self.image_detail_var.get() # Get image detail

       # --- Construct Payload ---
       # Start with base payload, enable streaming
       payload = {"model": model, "stream": True}

       # Add optional parameters if they have meaningful values
       payload["temperature"] = temperature # Always include
       payload["top_p"] = top_p           # Always include
       if max_tokens is not None: payload["max_tokens"] = max_tokens
       if presence_penalty != 0.0: payload["presence_penalty"] = presence_penalty
       if frequency_penalty != 0.0: payload["frequency_penalty"] = frequency_penalty
       if stop_sequences: payload["stop"] = stop_sequences

       # --- Prepare Messages ---
       final_messages_for_request = []
       is_reasoning_model = any(r_kw in model.lower() for r_kw in ["r1", "z1", "qwq", "qwen3"])

       # 1. Add System Prompt (if provided and not a reasoning model)
       if system_prompt and not is_reasoning_model:
           final_messages_for_request.append({"role": "system", "content": system_prompt})
       elif is_reasoning_model and system_prompt: # Added condition to print only if system prompt was provided but skipped
            print("--- DEBUG: Reasoning model detected, skipping system message for request. ---")

       # 2. Add conversation history (user/assistant turns)
       # Make a deep copy to avoid modifying the original history when adding image data
       history_copy = json.loads(json.dumps(self.conversation_history))
       final_messages_for_request.extend(history_copy)


       # 3. Modify the *last* user message to include image data if applicable
       image_data_uri = None
       if image_path: # Prioritize local file
           image_data_uri = self._image_to_base64(image_path)
           if image_data_uri is None: # Handle conversion error
               self.after(0, self._set_status, "图片处理失败")
               self.after(0, self._toggle_controls, True)
               # Clear the failed path? Maybe not, let user retry or clear manually.
               # self.after(0, lambda: self.image_path_var.set(""))
               # self.after(0, lambda: self.image_path_label.config(text="未选择本地图片"))
               # Remove the last user message from history as the request failed
               if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                   self.conversation_history.pop()
               return # Stop request if image conversion failed
       elif image_url_from_input: # Use URL if no local file
           image_data_uri = image_url_from_input

       if final_messages_for_request and final_messages_for_request[-1]["role"] == "user":
           last_user_message = final_messages_for_request[-1]
           # Ensure content is treated as text initially
           last_user_content_text = last_user_message["content"]
           if isinstance(last_user_content_text, list): # If somehow it's already complex, extract text
                for item in last_user_content_text:
                     if item.get("type") == "text":
                         last_user_content_text = item.get("text", "")
                         break
                else: # If no text item found in list, default to empty string or handle error
                    last_user_content_text = ""


           is_vision_model = any(vl_kw in model.lower() for vl_kw in ["vl", "vision", "internvl"])

           if image_data_uri and is_vision_model:
               # Construct the complex content for the *request*
               image_content_part = {"type": "image_url", "image_url": {"url": image_data_uri}}
               if image_detail != "auto":
                   image_content_part["image_url"]["detail"] = image_detail

               new_content = [{"type": "text", "text": last_user_content_text}, image_content_part]

               # Handle InternVL specific order recommendation
               if "internvl" in model.lower():
                   new_content.reverse() # Put image first for InternVL

               last_user_message["content"] = new_content # Modify the message in the *request list*
           else:
                # Ensure content is just the text if no image or not vision model
                last_user_message["content"] = last_user_content_text


       payload["messages"] = final_messages_for_request

       headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
       print("--- DEBUG: Sending Payload ---") # Debug print
       print(json.dumps(payload, indent=2, ensure_ascii=False))
       print("--- END DEBUG ---")

       # --- Stream Handling ---
       full_assistant_response = ""
       accumulated_reasoning = ""
       is_first_content_chunk = True
       is_first_reasoning_chunk = True
       try:
           response = requests.post(CHAT_API_URL, json=payload, headers=headers, timeout=120, stream=True)
           response.raise_for_status() # Check for HTTP errors immediately

           for chunk_bytes in response.iter_lines(): # Use iter_lines for SSE
               if chunk_bytes:
                   chunk_str = chunk_bytes.decode('utf-8')
                   if chunk_str.startswith("data: "):
                       chunk_data_str = chunk_str[len("data: "):]
                       if chunk_data_str.strip() == "[DONE]":
                           print("--- DEBUG: Stream finished [DONE] ---")
                           break # End of stream
                       try:
                           chunk_json = json.loads(chunk_data_str)
                           # print(f"--- DEBUG: Received Chunk --- \n{chunk_json}\n --- END CHUNK ---") # Less verbose debug

                           delta = chunk_json.get('choices', [{}])[0].get('delta', {})
                           delta_content = delta.get('content')
                           delta_reasoning = delta.get('reasoning_content') # Check for reasoning content

                           if delta_content:
                               if is_first_content_chunk:
                                   # Display "AI: " prefix
                                   self.after(0, self._display_stream_start, "assistant")
                                   is_first_content_chunk = False
                               # Append content chunk
                               self.after(0, self._append_message_chunk, delta_content, "assistant")
                               full_assistant_response += delta_content # Accumulate full response

                           if delta_reasoning:
                               if is_first_reasoning_chunk:
                                   # Display "System: " prefix for reasoning
                                   self.after(0, self._display_stream_start, "system")
                                   is_first_reasoning_chunk = False
                               # Append reasoning chunk
                               self.after(0, self._append_message_chunk, delta_reasoning, "system")
                               accumulated_reasoning += delta_reasoning # Accumulate reasoning

                       except json.JSONDecodeError:
                           print(f"--- DEBUG: Failed to decode JSON chunk: {chunk_data_str} ---")
                           self.after(0, self._display_message, "error", f"接收到无效的数据块: {chunk_data_str}")
                       except Exception as chunk_e:
                            print(f"--- DEBUG: Error processing chunk: {chunk_e} ---")
                            # Check if the error is the specific after() error and handle it gracefully
                            if "got an unexpected keyword argument 'is_start_of_stream'" in str(chunk_e):
                                print("--- DEBUG: Ignoring known after() keyword argument error during stream processing. ---")
                            else:
                                self.after(0, self._display_message, "error", f"处理数据块时出错: {chunk_e}")


           # After stream finishes
           if not is_first_content_chunk: # If we displayed assistant content
               self.after(0, self._display_stream_end) # Add final newline for assistant response
               # Add the complete response to history
               if full_assistant_response:
                   # Store assistant message (simple text, reasoning is not part of history)
                   self.conversation_history.append({"role": "assistant", "content": full_assistant_response})
               self.after(0, self._set_status, "消息接收成功")
           elif not is_first_reasoning_chunk: # If we only displayed reasoning content
               self.after(0, self._display_stream_end) # Add final newline for reasoning response
               self.after(0, self._set_status, "推理内容接收成功")
           elif not full_assistant_response and not accumulated_reasoning: # No content and no reasoning received
                self.after(0, self._display_message, "error", "API 未返回任何内容。")
                self.after(0, self._set_status, "接收失败：空响应")

           # Note: Reasoning content is displayed during the stream, not added to history


       except requests.exceptions.RequestException as e:
           error_message = f"API 请求失败: {e}"
           if hasattr(e, 'response') and e.response is not None:
               try:
                   # Try to get error from stream response if possible (might not be JSON)
                   error_text = e.response.text
                   error_message += f"\n服务器响应: {error_text}"
               except Exception:
                    error_message += f"\n无法读取服务器响应。"
           # Display error in chat window and status bar
           self.after(0, self._display_message, "error", f"API 错误: {error_message}")
           self.after(0, self._set_status, "发送/接收失败")
           # Remove the last user message from history as the request failed
           if self.conversation_history and self.conversation_history[-1]["role"] == "user":
               self.conversation_history.pop()

       except Exception as e:
           error_msg = f"处理流式响应时发生意外错误: {e}"
           print(f"--- DEBUG: Stream processing error: {e} ---")
           self.after(0, self._display_message, "error", error_msg)
           self.after(0, self._set_status, "发送/接收失败")
           # Remove the last user message from history as the request failed
           if self.conversation_history and self.conversation_history[-1]["role"] == "user":
               self.conversation_history.pop()

       finally:
           self.after(0, self._toggle_controls, True)
           # Clear image path *after* the request attempt
           self.after(0, lambda: self.image_path_var.set(""))
           self.after(0, lambda: self.image_path_label.config(text="未选择本地图片"))
           # Keep URL for potential resend/modification
           # self.after(0, lambda: self.image_url_var.set(""))


# --- 启动应用 ---
if __name__ == "__main__":
    app = SiliconFlowSuiteApp()
    app.mainloop()