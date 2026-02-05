import openai
import json
import os

openai.api_key = "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" 

def grade_submission_with_ai(question_content: str, student_answer: str):
    
    prompt = f"""
    Bạn là một giáo viên nghiêm khắc nhưng công tâm. Hãy chấm điểm bài làm sau đây:
    
    --- ĐỀ BÀI ---
    {question_content}
    
    --- BÀI LÀM CỦA HỌC SINH ---
    {student_answer}
    
    --- YÊU CẦU ---
    1. Chấm điểm trên thang điểm 10.
    2. Đưa ra nhận xét ngắn gọn (tối đa 3 câu) về ưu điểm và lỗi sai.
    3. Trả về kết quả CHỈ dưới dạng JSON format như sau (không thêm lời dẫn):
    {{
        "score": <số điểm, ví dụ: 8.5>,
        "feedback": "<lời nhận xét>"
    }}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý hỗ trợ chấm thi."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()
        
        result = json.loads(content)
        return result

    except Exception as e:
        print(f"Lỗi khi gọi OpenAI: {e}")
        return {"score": 0, "feedback": "Lỗi hệ thống chấm điểm tự động."}