
document.addEventListener('DOMContentLoaded', function() {
    
    const quickResponseButtons = document.querySelectorAll('.quick-response');
    
    quickResponseButtons.forEach(button => {
        
        button.replaceWith(button.cloneNode(true));
    });
    
    
    setTimeout(() => {
        const newButtons = document.querySelectorAll('.quick-response');
        
        newButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                
                const responseType = this.getAttribute('data-response-type') || 
                                   this.querySelector('span').textContent;
                
                
                const chatInput = document.getElementById('messageInput') || 
                                document.getElementById('userInput');
                
                if (chatInput) {
                    
                    let responseText = '';
                    
                    switch(responseType.toLowerCase()) {
                        case 'ask for symptom details':
                        case 'symptom':
                            responseText = "I understand you're asking about symptoms. Could you please describe them in more detail? (e.g., location, severity, duration, triggers)";
                            break;
                        case 'medication disclaimer':
                        case 'medication':
                            responseText = "For medication information, please consult with a healthcare provider who knows your medical history. They can consider: your specific condition, other medications, allergies, and medical history. Never change medication without professional advice.";
                            break;
                        case 'emergency response':
                        case 'emergency':
                            responseText = "🚨 EMERGENCY: If this is a medical emergency, please:\n\n1. Call emergency services (911/112) immediately\n2. Do NOT wait for AI response\n3. Stay calm and follow instructions\n4. If alone, try to get help from neighbors\n\n⚠️ This AI cannot provide emergency medical care.";
                            break;
                    }
                    
                    if (responseText) {
                        chatInput.value = responseText;
                        
                        
                        const inputEvent = new Event('input', { bubbles: true });
                        chatInput.dispatchEvent(inputEvent);
                        
                        
                        chatInput.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                        chatInput.focus();
                        
                        
                        chatInput.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.5)';
                        setTimeout(() => {
                            chatInput.style.boxShadow = '';
                        }, 1000);
                    }
                }
            });
        });
    }, 100);
});