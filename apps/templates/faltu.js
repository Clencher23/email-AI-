//  <!-- <script>
//         function $(sel) { return document.querySelector(sel); }
//         let currentEmailData = null;

//         function showModal(modalId) { $(modalId).classList.add('active'); }
//         function hideModal(modalId) { $(modalId).classList.remove('active'); }

//         async function loadEmails() {
//             const enquiryList = $('#enquiryList');
//             enquiryList.innerHTML = "<li class='no-emails'>Loading...</li>";
//             try {
//                 const res = await fetch('/emails/list');
//                 const data = await res.json();
//                 enquiryList.innerHTML = "";
//                 if (Array.isArray(data) && data.length) {
//                     data.reverse().forEach(email => {
//                         const li = document.createElement('li');
//                         li.textContent = (email.subject || "(No Subject)") + " — " + (email.from || "");
//                         li.addEventListener('click', () => showEmailModal(email));
//                         enquiryList.appendChild(li);
//                     });
//                 } else {
//                     enquiryList.innerHTML = "<li class='no-emails'>No emails found.</li>";
//                 }
//             } catch (e) {
//                 enquiryList.innerHTML = "<li class='no-emails'>Failed to load emails.</li>";
//             }
//         }

//         async function showEmailModal(email) {
//             $('#threadDetailPanel').style.display = '';
//             $('#modal-from').textContent = email.from || "";
//             $('#modal-subject').textContent = email.subject || "";
//             $('#modal-date').textContent = formatDate(email.date || "");
//             $('#modal-body').innerHTML = "<div class='no-emails'>Loading email...</div>";
//             $('#modal-attachments').innerHTML = "";

//             try {
//                 const res = await fetch(`/emails/${email.id}`);
//                 const data = await res.json();
//                 currentEmailData = data;
//                 $('#modal-body').innerHTML = data.body
//                     ? DOMPurify.sanitize(data.body, { FORBID_TAGS: ['img'] })
//                     : "(No content)";
//                 // renderAttachments(data.attachments || [], '#modal-attachments'); // Optional
//             } catch (e) {
//                 $('#modal-body').innerHTML = "<div class='no-emails'>Failed to load email.</div>";
//             }
//         }


        

//         // function renderAttachments(attachments, containerSel) {
//         //     const attachDiv = $(containerSel);
//         //     attachDiv.innerHTML = "";
//         //     if (attachments.length) {
//         //         attachments.forEach(filename => {
//         //             const cleanName = filename.replace(/^\d+_/, "");
//         //             attachDiv.innerHTML += `<a href="/download/${filename}" class="attachment-link" target="_blank" download>📎 ${cleanName}</a>`;
//         //         });
//         //     }
//         // }

//         // function analyzeCurrentEmail() {
//         //     // Removed for now. To be restored when analysis endpoint is enabled
//         // }

//         $('#closeExtractModalBtn')?.addEventListener("click", () => hideModal('#extractModal'));

//         function formatDate(dateStr) {
//             if (!dateStr) return "";
//             const d = new Date(dateStr);
//             if (isNaN(d)) return dateStr;
//             const weekday = d.toLocaleString('en-US', { weekday: 'short' });
//             const day = d.getDate();
//             const month = d.toLocaleString('en-US', { month: 'short' }).toLowerCase();
//             const year = d.getFullYear();
//             const time = d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
//             return `${weekday}, ${day} ${month} ${year}, ${time}`;
//         }

//         document.addEventListener("DOMContentLoaded", function () {
//             loadEmails();
//         });
//     </script> -->



//  async function analyzeCurrentEmail() {
//             $('#modalOrderDetails').textContent = '';
//             $('#modalOrderXML').textContent = '';
//             document.getElementById("extractStats").textContent = '';
//             const analyzeBtn = $('#analyzeModalBtn');
//             if (!currentEmailData) return;
//             showModal('#extractModal');
//             analyzeBtn.disabled = true;
//             analyzeBtn.innerHTML = 'Thinking...';

//             const emailBody = currentEmailData.body || "";
//             const attachments = currentEmailData.attachments || [];
//             const formData = new FormData();
//             formData.append('text', emailBody);

//             const model = document.getElementById('modelSelect') ? document.getElementById('modelSelect').value : "groq";
//             formData.append('model', model);

//             for (const filename of attachments) {
//                 try {
//                     const res = await fetch(`/products/genai/email-ai-agent/download/${filename}`);
//                     const blob = await res.blob();
//                     const cleanName = filename.replace(/^\d+_/, "");
//                     formData.append('attachments', blob, cleanName);
//                 } catch (e) {
//                     console.warn('Could not fetch attachment:', filename, e);
//                 }
//             }

//             const startTime = Date.now();
//             $('#modalOrderDetails').textContent = "Analyzing...";
//             $('#modalOrderXML').textContent = "Analyzing...";
//             document.getElementById("extractStats").textContent = "";

//             try {
//                 const res = await fetch('/products/genai/email-ai-agent/analyze-order', {
//                     method: 'POST',
//                     body: formData
//                 });

//                 // Streaming SSE parsing:
//                 if (!res.body) throw new Error("No response stream!");
//                 const reader = res.body.getReader();
//                 let decoder = new TextDecoder('utf-8');
//                 let partialBuffer = '';
//                 let plainText = '';
//                 let xmlText = '';
//                 let done = false;
//                 let buffer = '';

//                 // For UI: clear fields, show progress
//                 $('#modalOrderDetails').textContent = '';
//                 $('#modalOrderXML').textContent = '';
//                 document.getElementById("extractStats").textContent = 'Analyzing...';

//                 // Helper: process each SSE line as it arrives
//                 while (!done) {
//                     const { value, done: streamDone } = await reader.read();
//                     if (streamDone) break;
//                     buffer += decoder.decode(value, { stream: true });

//                     // Split buffer into complete lines (SSE sends \n\n after each message)
//                     let lines = buffer.split('\n\n');
//                     buffer = lines.pop(); // keep last (maybe incomplete) in buffer 

//                     for (let line of lines) {
//                         if (!line.startsWith('data:')) continue;
//                         let dataLine = line.replace(/^data:\s*/, '').trim();
//                         if (!dataLine) continue;

//                         let payload;
//                         try { payload = JSON.parse(dataLine); }
//                         catch (e) { continue; }

//                         if (payload.type === "partial" && payload.data) {
//                             // You may want to accumulate partialBuffer or display live
//                             partialBuffer += payload.data;
//                             $('#modalOrderDetails').textContent = partialBuffer;
//                         }
//                         if (payload.type === "final") {
//                             plainText = payload.plain_text || '';
//                             xmlText = payload.xml || '';
//                             // Show the result
//                             showExtractModal(plainText, xmlText);

//                             // Time
//                             const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
//                             document.getElementById("extractStats").innerHTML = `Time Taken: <b>${elapsed}s</b>`;
//                         }
//                     }
//                 }

//                 analyzeBtn.disabled = false;
//                 analyzeBtn.innerHTML = 'Analyze Email';

//             } catch (e) {
//                 $('#modalOrderDetails').textContent = "Error analyzing email.";
//                 showModal('#extractModal');
//                 document.getElementById("extractStats").textContent = "";
//                 analyzeBtn.disabled = false;
//                 analyzeBtn.innerHTML = 'Analyze Email';
//             }
//         }





// function showExtractModal(plainText, xmlText) {
//             $('#modalOrderDetails').textContent = plainText || '';
//             $('#modalOrderDetails').style.display = 'block';
//             $('#modalOrderXML').textContent = xmlText || '';
//             $('#modalOrderXML').style.display = 'none';

//             $('#extractModal').onclick = (e) => {
//                 if (e.target === $('#extractModal')) hideModal('#extractModal');

//             };

//             // Tab logic
//             $('#plainTabBtn').classList.add('active');
//             $('#xmlTabBtn').classList.remove('active');
//             $('#plainTabBtn').onclick = function () {
//                 $('#plainTabBtn').classList.add('active');
//                 $('#xmlTabBtn').classList.remove('active');
//                 $('#modalOrderDetails').style.display = 'block';
//                 $('#modalOrderXML').style.display = 'none';
//             };
//             $('#xmlTabBtn').onclick = function () {
//                 $('#xmlTabBtn').classList.add('active');
//                 $('#plainTabBtn').classList.remove('active');
//                 $('#modalOrderDetails').style.display = 'none';
//                 $('#modalOrderXML').style.display = 'block';
//             };

//             // Clear stats (speed) each open, to avoid stale value if error
//             document.getElementById("extractStats").textContent = "";

//             showModal('#extractModal');
//         }