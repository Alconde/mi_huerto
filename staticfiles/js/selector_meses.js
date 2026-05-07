/**
 * Selector Inteligente de Meses para Formulario de Cultivos
 * Permite seleccionar meses mediante checkboxes y sincroniza con campo de texto
 */

document.addEventListener('DOMContentLoaded', function() {
    // Crear contenedor para selector de meses si los campos existen
    const campos_meses = {
        'siembra': document.querySelector('[name="meses_siembra"]'),
        'trasplante': document.querySelector('[name="meses_trasplante"]'),
        'recoleccion': document.querySelector('[name="meses_recoleccion"]')
    };
    
    // Información de meses
    const meses = [
        { num: 1, nombre: 'Enero', emoji: '❄️' },
        { num: 2, nombre: 'Febrero', emoji: '🌡️' },
        { num: 3, nombre: 'Marzo', emoji: '🌸' },
        { num: 4, nombre: 'Abril', emoji: '🌷' },
        { num: 5, nombre: 'Mayo', emoji: '🌼' },
        { num: 6, nombre: 'Junio', emoji: '☀️' },
        { num: 7, nombre: 'Julio', emoji: '🌞' },
        { num: 8, nombre: 'Agosto', emoji: '🌞' },
        { num: 9, nombre: 'Septiembre', emoji: '🍂' },
        { num: 10, nombre: 'Octubre', emoji: '🎃' },
        { num: 11, nombre: 'Noviembre', emoji: '🍁' },
        { num: 12, nombre: 'Diciembre', emoji: '❄️' }
    ];
    
    // Crear tooltip con selector visual
    Object.keys(campos_meses).forEach(tipo => {
        const campo = campos_meses[tipo];
        if (!campo) return;
        
        // Crear botón para abrir selector
        const btn_selector = document.createElement('button');
        btn_selector.type = 'button';
        btn_selector.className = 'btn btn-sm btn-outline-secondary ms-2';
        btn_selector.textContent = '📅 Selector Visual';
        btn_selector.setAttribute('data-tipo', tipo);
        
        // Insertar botón después del campo
        campo.parentNode.appendChild(btn_selector);
        
        // Crear modal con selector
        btn_selector.addEventListener('click', (e) => {
            e.preventDefault();
            mostrarSelectorMeses(campo, tipo, meses);
        });
        
        // Parsear valores existentes
        actualizarCampoDesdeTexto(campo);
    });
    
    function mostrarSelectorMeses(campo, tipo, meses) {
        // Obtener meses seleccionados actuales
        const valores_actuales = campo.value ? 
            campo.value.split(',').map(m => parseInt(m.trim())).filter(m => m > 0) : [];
        
        // Crear HTML del modal
        let html = `
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); 
                        display: flex; align-items: center; justify-content: center; z-index: 9999;" 
                 class="modal-overlay">
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; 
                            box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                    <h5 style="margin-bottom: 20px; color: #2e7d32; font-weight: bold;">
                        Selecciona Meses para ${tipo.toUpperCase()}
                    </h5>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
        `;
        
        meses.forEach(mes => {
            const checked = valores_actuales.includes(mes.num) ? 'checked' : '';
            html += `
                <label style="display: flex; align-items: center; padding: 10px; border: 1px solid #e0e0e0; 
                             border-radius: 6px; cursor: pointer; transition: all 0.3s;" 
                       class="mes-checkbox">
                    <input type="checkbox" value="${mes.num}" ${checked} 
                           style="width: 18px; height: 18px; cursor: pointer; margin-right: 8px;">
                    <span>${mes.emoji} ${mes.nombre}</span>
                </label>
            `;
        });
        
        html += `
                    </div>
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button type="button" class="btn btn-secondary btn-cancel">Cancelar</button>
                        <button type="button" class="btn btn-success btn-guardar">Guardar</button>
                    </div>
                </div>
            </div>
        `;
        
        // Crear elemento temporalmente
        const modal_div = document.createElement('div');
        modal_div.innerHTML = html;
        document.body.appendChild(modal_div);
        
        // Eventos
        const overlay = modal_div.querySelector('.modal-overlay');
        const btn_guardar = modal_div.querySelector('.btn-guardar');
        const btn_cancelar = modal_div.querySelector('.btn-cancel');
        
        btn_guardar.addEventListener('click', () => {
            const checkboxes = modal_div.querySelectorAll('.mes-checkbox input:checked');
            const meses_seleccionados = Array.from(checkboxes)
                .map(cb => cb.value)
                .sort((a, b) => a - b)
                .join(',');
            
            campo.value = meses_seleccionados;
            campo.dispatchEvent(new Event('change'));
            modal_div.remove();
        });
        
        btn_cancelar.addEventListener('click', () => modal_div.remove());
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) modal_div.remove();
        });
    }
    
    function actualizarCampoDesdeTexto(campo) {
        campo.addEventListener('change', () => {
            // Validación en tiempo real
            const valor = campo.value;
            if (!valor) return;
            
            try {
                const meses = valor.split(',').map(m => {
                    const n = parseInt(m.trim());
                    if (n < 1 || n > 12) throw new Error(`Mes ${n} inválido`);
                    return n;
                });
                campo.classList.remove('is-invalid');
                campo.classList.add('is-valid');
            } catch (e) {
                campo.classList.add('is-invalid');
                campo.classList.remove('is-valid');
            }
        });
    }
});
