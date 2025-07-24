# import os
# import base64
# import io
# from dotenv import load_dotenv
# from groq import Groq

# # from services.img_util import compress_image_to_target_size
# # from services.pdf_util import pdf_pages_to_base64_images

# load_dotenv()
# GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY not set in environment or .env file!")
# LLAMA_SCOUT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# client = Groq(api_key=GROQ_API_KEY)

def file_to_data_url(b64_string):
    return f"data:image/jpeg;base64,{b64_string}"

# def make_prompt():
    return (
        "You are an AI assistant for order management. Extract structured order information from the text or image as a JSON object with these keys:\n"
        "- customer_id (or account)\n"
        "- customer_name\n"
        "- order_date\n"
        "- products (array of objects, each with: product_code, description, quantity, unit, price if present)\n"
        "If a field is missing, use null. For products, always extract quantity and description if present.\n"
        "If multiple product rows are present, extract all as separate items in the products array.\n"
        "If you receive both a text and an image, and each contains information about a different order/customer, extract each as a separate JSON object inside a JSON array. Never merge two distinct orders or customers into a single object.\n"
        "Return ONLY a single JSON object, or if there are multiple distinct orders or customers, return a JSON array of such objects. Do not include explanations or markdown formatting."
    )

# def try_parse_json(raw):
#     import json
#     if not raw: return None
#     raw = raw.strip().replace('```json', '').replace('```', '').strip()
#     try:
#         return json.loads(raw)
#     except Exception:
#         return None

# def order_to_plaintext(order):
#     if not order: return ""
#     out = []
#     if isinstance(order, list):
#         for idx, o in enumerate(order):
#             out.append(f"Order {idx+1}:\n" + order_to_plaintext(o))
#         return "\n\n".join(out)
#     if order.get("customer_id") or order.get("customer_name") or order.get("order_date"):
#         out.append(
#             (f'Customer ID: {order.get("customer_id")}\n' if order.get("customer_id") else '') +
#             (f'Customer Name: {order.get("customer_name")}\n' if order.get("customer_name") else '') +
#             (f'Order Date: {order.get("order_date")}\n' if order.get("order_date") else '')
#         )
#     if isinstance(order.get("products"), list) and order["products"]:
#         out.append("Products:")
#         for idx, prod in enumerate(order["products"]):
#             out.append(
#                 f"  {idx+1}. " +
#                 (f"Product Code: {prod.get('product_code')}; " if prod.get('product_code') else "") +
#                 (f"Description: {prod.get('description')}; " if prod.get('description') else "") +
#                 (f"Quantity: {prod.get('quantity')}; " if prod.get('quantity') else "") +
#                 (f"Unit: {prod.get('unit')}; " if prod.get('unit') else "") +
#                 (f"Price: {prod.get('price')};" if prod.get('price') else "")
#             )
#     return "\n".join(out)

# # def analyze_order_ai(body=None, files=None):
#     messages = [{"role": "system", "content": make_prompt()}]
#     sources = []

#     if body and body.strip():
#         messages.append({"role": "user", "content": body})
#         sources.append("body")

#     image_contents = []
#     if files:
#         for file in files:
#             filename = ""
#             file_bytes = None
#             if hasattr(file, "read"):
#                 filename = getattr(file, "filename", "").lower()
#                 file.seek(0)
#                 file_bytes = file.read()
#             elif isinstance(file, dict) and "filename" in file and "bytes" in file:
#                 filename = file["filename"].lower()
#                 file_bytes = file["bytes"]
#             else:
#                 continue

#             if filename.endswith('.pdf') or (file_bytes and file_bytes[:4] == b'%PDF'):
#                 try:
#                     pdf_img_b64s = pdf_pages_to_base64_images(io.BytesIO(file_bytes))
#                     for img_b64 in pdf_img_b64s:
#                         compressed_b64 = compress_image_to_target_size(img_b64)
#                         data_url = file_to_data_url(compressed_b64)
#                         image_contents.append({"type": "image_url", "image_url": {"url": data_url}})
#                         sources.append(f"{filename} (pdf page)")
#                 except Exception as e:
#                     sources.append(f"{filename} (pdf conversion error: {e})")
#             else:
#                 try:
#                     img_b64 = base64.b64encode(file_bytes).decode("utf-8")
#                     compressed_b64 = compress_image_to_target_size(img_b64)
#                     data_url = file_to_data_url(compressed_b64)
#                     image_contents.append({"type": "image_url", "image_url": {"url": data_url}})
#                     sources.append(filename)
#                 except Exception as e:
#                     sources.append(f"{filename} (image conversion error: {e})")

#     if image_contents:
#         messages.append({"role": "user", "content": image_contents})

#     if len(messages) == 1:
#         yield {
#             "plain_text": None,
#             "xml": None,
#             "error": "No input provided",
#             "source": sources
#         }
#         return

#     try:
#         response = client.chat.completions.create(
#             model=LLAMA_SCOUT_MODEL,
#             messages=messages,
#             temperature=0.2,
#             max_tokens=1024,
#             top_p=1,
#             stream=True  # STREAMING!
#         )

#         # Accumulate the response as it streams in
#         content_accum = ""
#         for chunk in response:
#             # For OpenAI/Groq compatible streaming APIs
#             part = chunk.choices[0].delta.content or ""
#             if part:
#                 content_accum += part
#                 yield {"type": "partial", "data": part}

#         # At the end, you can parse full data and yield plain/xml forms
#         json_data = try_parse_json(content_accum)
#         plain = order_to_plaintext(json_data)
#         xml = json_to_xml(json_data) if json_data else None

#         yield {
#             "type": "final",
#             "plain_text": plain,
#             "xml": xml,
#             "error": None,
#             "source": sources
#         }
#     except Exception as e:
        
#         import traceback
#         print("exception", e)
#         traceback.print_exc()
#         yield {
#             "plain_text": None,
#             "xml": None,
#             "error": str(e),
#             "source": sources
#         }


import os
import base64
import io
from dotenv import load_dotenv
from groq import Groq

from apps.services.img_util import compress_image_to_target_size
from apps.services.pdf_util import pdf_pages_to_base64_images

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in environment or .env file!")

LLAMA_SCOUT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
client = Groq(api_key=GROQ_API_KEY)

def file_to_data_url(b64_string):
    return f"data:image/jpeg;base64,{b64_string}"

def analyze_email_ai(subject, sender, body=None, files=None, action="analyze"):
    """
    Stream-based AI function that either:
    - summarizes the email (action='analyze'), or
    - drafts a reply (action='draft_reply')
    """

    if not body and not files:
        yield {
            "error": "No email content or attachments provided.",
            "type": "error"
        }
        return

    # 📦 Build initial prompt message
    system_prompt = "You are an AI assistant that helps users understand and respond to business emails."
    user_prompt = f"Subject: {subject}\nFrom: {sender}\n\n{body.strip() if body else ''}"

    image_contents = []
    sources = []

    if files:
        for file in files:
            filename = ""
            file_bytes = None

            if hasattr(file, "read"):
                filename = getattr(file, "filename", "").lower()
                file.seek(0)
                file_bytes = file.read()
            elif isinstance(file, dict) and "filename" in file and "bytes" in file:
                filename = file["filename"].lower()
                file_bytes = file["bytes"]
            else:
                continue

            if filename.endswith('.pdf') or (file_bytes and file_bytes[:4] == b'%PDF'):
                try:
                    pdf_img_b64s = pdf_pages_to_base64_images(io.BytesIO(file_bytes))
                    for img_b64 in pdf_img_b64s:
                        compressed_b64 = compress_image_to_target_size(img_b64)
                        data_url = file_to_data_url(compressed_b64)
                        image_contents.append({"type": "image_url", "image_url": {"url": data_url}})
                        sources.append(f"{filename} (pdf page)")
                except Exception as e:
                    sources.append(f"{filename} (pdf conversion error: {e})")
            else:
                try:
                    img_b64 = base64.b64encode(file_bytes).decode("utf-8")
                    compressed_b64 = compress_image_to_target_size(img_b64)
                    data_url = file_to_data_url(compressed_b64)
                    image_contents.append({"type": "image_url", "image_url": {"url": data_url}})
                    sources.append(filename)
                except Exception as e:
                    sources.append(f"{filename} (image conversion error: {e})")

    # 🧠 Final prompt message
    if action == "analyze":
        task = "Summarize the following email in 2-4 sentences. Mention the main purpose, sender’s intent, and important points briefly."
    elif action == "draft_reply":
        task = "Write a professional and polite reply to the following email on behalf of the recipient."
    else:
        yield {
            "error": "Invalid action. Must be 'analyze' or 'draft_reply'.",
            "type": "error"
        }
        return

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{task}\n\n{user_prompt}"}
    ]

    if image_contents:
        messages.append({"role": "user", "content": image_contents})

    try:
        response = client.chat.completions.create(
            model=LLAMA_SCOUT_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
            top_p=1,
            stream=True
        )

        content_accum = ""
        for chunk in response:
            part = chunk.choices[0].delta.content or ""
            if part:
                content_accum += part
                yield {"type": "partial", "data": part}

        yield {
            "type": "final",
            "text": content_accum.strip(),
            "source": sources
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield {
            "type": "error",
            "error": str(e),
            "source": sources
        }
