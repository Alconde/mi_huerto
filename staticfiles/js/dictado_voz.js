// static/js/dictado_voz.js
document.addEventListener('DOMContentLoaded', function() {
    const obsField = document.getElementById('id_observaciones');
    if (obsField) {
        const btn = document.createElement('button');
        btn.innerHTML = "🎤 Dictar nota";
        btn.type = "button";
        btn.className = "btn btn-sm btn-outline-secondary ms-2";
        btn.onclick = () => {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'es-ES';
            recognition.onresult = (event) => {
                obsField.value += " " + event.results[0][0].transcript;
            };
            recognition.start();
        };
        obsField.parentNode.insertBefore(btn, obsField.nextSibling);
    }
});