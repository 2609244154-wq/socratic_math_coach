"""
苏格拉底数学教练 - 核心AI逻辑模块
处理数学题目分析、OCR识别、AI对话引导
"""

import os
import json
import base64
from io import BytesIO
from typing import Optional, Dict, Any, List
import requests
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import streamlit as st
import time
import re

# 加载环境变量
load_dotenv()

class SocraticMathCoach:
    """苏格拉底式数学解题教练"""
    
    def __init__(self):
        """初始化教练"""
        # 从环境变量或Streamlit Secrets获取API密钥
        self.api_key = self._get_api_key()
        self.api_available = bool(self.api_key)
        
        # 智谱AI API配置
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-4-flash"  # 免费模型，速度快
        
        # 对话历史
        self.chat_history = []
        
        # 题目分析结果
        self.problem_analysis = {
            "original_text": "",
            "ocr_text": "",
            "full_text": "",
            "has_image": False,
            "knowledge_points": [],
            "difficulty": "unknown"
        }
        
        # 初始化OCR
        self.ocr_enabled = self._check_ocr_availability()
        
        # 系统提示词
        self.system_prompt = """你是一位苏格拉底式的数学教练，专门通过提问引导学生自己找到答案。

你的教学原则：
1. ❌ 永远不要直接给出答案或完整解法
2. ✅ 通过提问引导学生思考
3. ✅ 根据学生水平调整问题难度
4. ✅ 在学生卡住时给予提示而非答案
5. ✅ 鼓励学生解释自己的思考过程
6. ✅ 保持耐心、支持和积极的态度

引导策略：
1. 先问学生对题目的理解
2. 引导学生识别已知条件和未知量
3. 帮助学生回忆相关数学概念
4. 引导学生建立解题思路
5. 鼓励尝试不同的方法
6. 引导学生验证答案

记住：你的目标是培养学生独立解决问题的能力，而不是替他们解决问题。"""
    
    def _get_api_key(self) -> str:
        """获取API密钥，优先从Streamlit Secrets，然后从环境变量"""
        # 首先尝试从Streamlit Secrets获取
        try:
            if hasattr(st, "secrets"):
                if "ZHIPUAI_API_KEY" in st.secrets:
                    return st.secrets["ZHIPUAI_API_KEY"]
        except:
            pass
        
        # 然后从环境变量获取
        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        
        # 如果环境变量没有，检查是否有直接的输入
        if not api_key:
            # 尝试从会话状态获取
            if hasattr(st, "session_state"):
                if "api_key" in st.session_state:
                    api_key = st.session_state.api_key
        
        return api_key
    
    def update_api_key(self, new_api_key: str):
        """更新API密钥"""
        self.api_key = new_api_key
        self.api_available = bool(new_api_key)
        os.environ["ZHIPUAI_API_KEY"] = new_api_key
        
        if hasattr(st, "session_state"):
            st.session_state.api_key = new_api_key
    
    def _check_ocr_availability(self) -> bool:
        """检查OCR功能是否可用"""
        try:
            # 检查pytesseract是否可用
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def analyze_problem(self, text: str = "", image_bytes: bytes = None) -> Dict[str, Any]:
        """分析题目，提取信息"""
        # 提取图片中的文字
        ocr_text = ""
        if image_bytes and self.ocr_enabled:
            try:
                # 使用PIL打开图片
                image = Image.open(BytesIO(image_bytes))
                
                # 预处理图片：转换为灰度
                if image.mode != 'L':
                    image = image.convert('L')
                
                # OCR识别
                ocr_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                ocr_text = self._clean_ocr_text(ocr_text)
                
            except Exception as e:
                print(f"OCR识别失败: {e}")
                # 如果不使用Streamlit，可以记录日志
                if hasattr(st, "warning"):
                    st.warning(f"OCR识别失败: {e}")
        
        # 合并文本
        full_text = text
        if ocr_text:
            if full_text:
                full_text += "\n\n从图片中识别:\n" + ocr_text
            else:
                full_text = ocr_text
        
        # 分析题目难度和知识点
        knowledge_points = self._extract_knowledge_points(full_text)
        difficulty = self._estimate_difficulty(full_text)
        
        # 保存分析结果
        self.problem_analysis = {
            "original_text": text,
            "ocr_text": ocr_text,
            "full_text": full_text,
            "has_image": image_bytes is not None,
            "knowledge_points": knowledge_points,
            "difficulty": difficulty
        }
        
        return self.problem_analysis
    
    def _clean_ocr_text(self, text: str) -> str:
        """清理OCR识别结果"""
        if not text:
            return ""
        
        # 清理常见OCR错误
        corrections = {
            "。": ".",
            "，": ",",
            "：": ":",
            "；": ";",
            "！": "!",
            "？": "?",
            "（": "(",
            "）": ")",
            "【": "[",
            "】": "]",
            "《": "<",
            "》": ">",
            "＂": '"',
            "＇": "'",
            "﹁": '"',
            "﹂": '"',
            "﹃": '"',
            "﹄": '"',
        }
        
        for wrong, right in corrections.items():
            text = text.replace(wrong, right)
        
        # 移除多余空格和空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 合并短行
        merged_lines = []
        current_line = ""
        for line in lines:
            if len(line) < 20 and not line.endswith(('.', '?', '!', '。', '？', '！')):
                current_line = current_line + " " + line if current_line else line
            else:
                if current_line:
                    merged_lines.append(current_line)
                merged_lines.append(line)
                current_line = ""
        
        if current_line:
            merged_lines.append(current_line)
        
        return '\n'.join(merged_lines)
    
    def _extract_knowledge_points(self, text: str) -> List[str]:
        """从题目中提取知识点"""
        if not text:
            return []
        
        # 常见数学知识点关键词
        knowledge_keywords = {
            "勾股定理": ["勾股", "直角三角形", "a²+b²=c²", "斜边", "直角边"],
            "一元二次方程": ["二次方程", "x²", "ax²+bx+c", "求根", "判别式"],
            "一次函数": ["一次函数", "y=kx+b", "斜率", "截距"],
            "二次函数": ["二次函数", "抛物线", "顶点", "对称轴"],
            "相似三角形": ["相似", "比例", "对应边", "对应角"],
            "全等三角形": ["全等", "SSS", "SAS", "ASA"],
            "平行四边形": ["平行四边形", "对边平行", "对角线"],
            "圆": ["圆", "半径", "直径", "圆周", "圆心"],
            "概率": ["概率", "可能性", "随机"],
            "统计": ["平均数", "中位数", "众数", "方差"],
            "三角函数": ["sin", "cos", "tan", "正弦", "余弦", "正切"],
            "导数": ["导数", "微分", "f'(x)"],
            "积分": ["积分", "∫", "定积分"],
            "向量": ["向量", "矢量", "点积", "叉积"],
            "复数": ["复数", "虚数", "i²=-1"],
            "数列": ["数列", "等差数列", "等比数列"],
            "不等式": ["不等式", "大于", "小于", "≥", "≤"],
            "几何证明": ["证明", "求证", "∴", "∵"],
        }
        
        # 转换为小写便于匹配
        text_lower = text.lower()
        
        # 匹配知识点
        matched_points = []
        for point, keywords in knowledge_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if point not in matched_points:
                        matched_points.append(point)
                    break
        
        return matched_points
    
    def _estimate_difficulty(self, text: str) -> str:
        """估计题目难度"""
        if not text:
            return "unknown"
        
        length = len(text)
        keywords_complex = ["证明", "求证", "推导", "解析", "复杂", "综合"]
        keywords_simple = ["计算", "求解", "等于", "求值"]
        
        text_lower = text.lower()
        
        # 检查复杂关键词
        has_complex = any(keyword in text_lower for keyword in keywords_complex)
        has_simple = any(keyword in text_lower for keyword in keywords_simple)
        
        if length > 200 or has_complex:
            return "hard"
        elif length > 50 or (has_complex and has_simple):
            return "medium"
        else:
            return "easy"
    
    def _call_glm_api(self, messages: list, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """调用智谱GLM API"""
        if not self.api_key or not self.api_available:
            return "请先在侧边栏设置智谱AI API密钥。获取地址：https://open.bigmodel.cn/"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "API返回格式异常"
            else:
                error_msg = f"API调用失败: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    if "error" in error_detail:
                        error_msg += f" - {error_detail['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                # 特定错误处理
                if response.status_code == 401:
                    return "API密钥无效或已过期。请检查并重新设置。"
                elif response.status_code == 429:
                    return "请求过于频繁，请稍后再试。"
                elif response.status_code == 503:
                    return "智谱AI服务暂时不可用，请稍后再试。"
                elif response.status_code >= 500:
                    return "服务器内部错误，请稍后重试。"
                
                return f"错误: {error_msg}"
                
        except requests.exceptions.Timeout:
            return "请求超时，请检查网络连接后重试。"
        except requests.exceptions.ConnectionError:
            return "网络连接失败，请检查网络设置。"
        except Exception as e:
            return f"未知错误: {str(e)}"
    
    def chat_with_student(self, student_input: str) -> str:
        """与学生对话，生成引导性问题"""
        if not self.api_key or not self.api_available:
            return "请先在侧边栏设置智谱AI API密钥才能继续对话。"
        
        # 构建消息历史
        messages = []
        
        # 添加系统提示词
        system_prompt_with_context = self.system_prompt + f"""

当前题目：{self.problem_analysis.get('full_text', '未知题目')}
涉及知识点：{', '.join(self.problem_analysis.get('knowledge_points', []))}
题目难度：{self.problem_analysis.get('difficulty', 'unknown')}

学生刚才说：{student_input}

请根据以上信息，生成一个引导性问题或提示。"""
        
        messages.append({"role": "system", "content": system_prompt_with_context})
        
        # 添加上下文历史（最近6轮对话）
        for msg in self.chat_history[-6:]:
            messages.append(msg)
        
        # 添加当前学生输入
        messages.append({"role": "user", "content": student_input})
        
        # 调用API
        response = self._call_glm_api(messages, temperature=0.6, max_tokens=800)
        
        # 保存对话历史
        self.chat_history.append({"role": "user", "content": student_input})
        self.chat_history.append({"role": "assistant", "content": response})
        
        # 限制历史记录长度
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
        
        return response
    
    def generate_hint(self) -> str:
        """生成提示（不依赖对话历史）"""
        if not self.api_key or not self.api_available:
            return "请先设置API密钥"
        
        hint_prompt = f"""你是一位有经验的数学老师，需要给学生一个恰到好处的提示。

题目：{self.problem_analysis.get('full_text', '未知题目')}
知识点：{', '.join(self.problem_analysis.get('knowledge_points', []))}

请生成一个引导性的提示，帮助学生继续思考，但不要直接给出答案。提示应该：
1. 指向解决问题的关键点
2. 提醒相关的数学概念或公式
3. 建议一个思考方向
4. 保持积极和支持的语气
5. 尽量简短，不超过2句话

例如："想想这个图形有什么特殊的性质？" 或 "你记得解决这类问题的常用方法吗？"

请生成提示："""
        
        messages = [
            {"role": "system", "content": "你是一位擅长给出恰到好处提示的数学老师。"},
            {"role": "user", "content": hint_prompt}
        ]
        
        return self._call_glm_api(messages, temperature=0.5, max_tokens=200)
    
    def check_solution(self, student_solution: str) -> str:
        """检查学生答案，但不直接说对错"""
        if not self.api_key or not self.api_available:
            return "请先设置API密钥"
        
        check_prompt = f"""题目：{self.problem_analysis.get('full_text', '未知题目')}
学生给出的答案/解法：{student_solution}

请检查学生的答案，但不直接说对错。而是：
1. 首先肯定学生的思考
2. 如果答案正确，让学生解释推理过程
3. 如果答案有误，引导学生发现错误
4. 鼓励学生自我检查
5. 提供进一步的思考方向

请用引导的方式回应："""
        
        messages = [
            {"role": "system", "content": "你是一位细心的数学老师，帮助学生验证答案。"},
            {"role": "user", "content": check_prompt}
        ]
        
        return self._call_glm_api(messages, temperature=0.4, max_tokens=500)
    
    def explain_concept(self, concept: str) -> str:
        """解释数学概念"""
        if not self.api_key or not self.api_available:
            return "请先设置API密钥"
        
        explain_prompt = f"""请用简单易懂的方式解释数学概念：{concept}

要求：
1. 用生活中的例子说明
2. 给出直观的理解
3. 说明这个概念的用途
4. 避免过于专业的术语
5. 适合中学生理解

请开始解释："""
        
        messages = [
            {"role": "system", "content": "你是一位擅长用简单例子解释复杂概念的数学老师。"},
            {"role": "user", "content": explain_prompt}
        ]
        
        return self._call_glm_api(messages, temperature=0.5, max_tokens=400)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取当前会话的摘要"""
        return {
            "problem_text": self.problem_analysis.get("full_text", "")[:100] + "..." if len(self.problem_analysis.get("full_text", "")) > 100 else self.problem_analysis.get("full_text", ""),
            "knowledge_points": self.problem_analysis.get("knowledge_points", []),
            "difficulty": self.problem_analysis.get("difficulty", "unknown"),
            "conversation_turns": len(self.chat_history) // 2,
            "has_image": self.problem_analysis.get("has_image", False)
        }