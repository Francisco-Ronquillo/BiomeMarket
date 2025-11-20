/* Chatbot widget minimal
   - crea un widget flotante
   - envía mensajes a /chatbot/api/
   - muestra respuestas y botones para agregar productos
*/
(function(){
  // CSS rápido
  const style = document.createElement('style');
  style.innerHTML = `
    :root{--bm-accent:#1f7a4c;--bm-accent-2:#2b8a3e;--bm-bg:#ffffff;--bm-ghost:#f3f5f7;--bm-text:#222;--bm-muted:#6b7280}
    .bm-chatbot-button{position:fixed;right:24px;bottom:24px;background:linear-gradient(135deg,var(--bm-accent-2),var(--bm-accent));color:#fff;border-radius:14px;width:64px;height:64px;border:none;cursor:pointer;z-index:9999;font-size:26px;box-shadow:0 10px 30px rgba(15,23,42,0.25);display:flex;align-items:center;justify-content:center;transition:transform .18s ease}
    .bm-chatbot-button:hover{transform:translateY(-3px) scale(1.03)}
    .bm-chatbot-panel{position:fixed;right:24px;bottom:100px;width:360px;max-width:calc(100% - 48px);height:520px;background:var(--bm-bg);border-radius:14px;box-shadow:0 18px 48px rgba(15,23,42,0.25);z-index:9999;display:flex;flex-direction:column;overflow:hidden;font-family:Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial}
    .bm-chatbot-header{display:flex;align-items:center;gap:10px;padding:14px 14px;background:linear-gradient(90deg,rgba(43,138,62,0.06),transparent);border-bottom:1px solid rgba(15,23,42,0.04)}
    .bm-chatbot-brand{display:flex;align-items:center;gap:10px}
    .bm-chatbot-avatar{width:40px;height:40px;border-radius:8px;background:var(--bm-accent);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;box-shadow:0 6px 18px rgba(15,23,42,0.12)}
    .bm-chatbot-title{font-weight:600;color:var(--bm-text);font-size:15px}
    .bm-chatbot-sub{font-size:12px;color:var(--bm-muted)}
    .bm-chatbot-actions{margin-left:auto;display:flex;gap:8px}
    .bm-chatbot-actions button{background:#fff;border:1px solid rgba(15,23,42,0.06);padding:6px 10px;border-radius:8px;color:var(--bm-accent-2);cursor:pointer;font-weight:600}
    .bm-chatbot-messages{flex:1;padding:16px;overflow:auto;background:linear-gradient(180deg,var(--bm-ghost),transparent);font-size:14px}
    .bm-chatbot-input{display:flex;padding:12px;border-top:1px solid rgba(15,23,42,0.04);gap:8px;background:transparent}
    .bm-chatbot-input input{flex:1;padding:10px;border:1px solid rgba(15,23,42,0.06);border-radius:10px;outline:none;background:#fff;box-shadow:inset 0 1px 0 rgba(255,255,255,0.6)}
    .bm-chatbot-input button{margin-left:0;padding:10px 14px;background:var(--bm-accent);color:#fff;border:none;border-radius:10px;cursor:pointer;font-weight:700}
    .bm-options{display:flex;gap:8px;flex-wrap:wrap;padding:12px;border-top:1px solid rgba(15,23,42,0.04);background:transparent}
    .bm-option{flex:1 1 48%;padding:10px 12px;background:linear-gradient(90deg,var(--bm-accent-2),var(--bm-accent));color:#fff;border:none;border-radius:10px;cursor:pointer;font-weight:700;text-align:center}
    .bm-option.ghost{background:#fff;color:var(--bm-accent-2);border:1px solid rgba(15,23,42,0.06)}
    .bm-auth-actions{display:flex;gap:8px;margin-top:10px}
    .bm-auth-btn{flex:1;padding:8px 10px;border-radius:8px;border:none;cursor:pointer;font-weight:700}
    .bm-auth-btn.primary{background:var(--bm-accent);color:#fff}
    .bm-auth-btn.secondary{background:#fff;border:1px solid rgba(15,23,42,0.06);color:var(--bm-accent-2)}
    .bm-msg{margin-bottom:12px;display:flex}
    .bm-msg.user{justify-content:flex-end}
    .bm-msg .bubble{display:inline-block;padding:10px 14px;border-radius:12px;max-width:78%;line-height:1.3;box-shadow:0 6px 18px rgba(11,15,21,0.06)}
    .bm-msg.user .bubble{background:linear-gradient(90deg,var(--bm-accent),var(--bm-accent-2));color:#fff;border-bottom-right-radius:6px}
    .bm-msg.bot .bubble{background:#fff;color:var(--bm-text);border-bottom-left-radius:6px;border:1px solid rgba(15,23,42,0.04)}
    .bm-msg .meta{display:block;font-size:11px;color:var(--bm-muted);margin-top:6px}
    .bm-product-item{border-radius:10px;padding:10px;margin:10px 0;background:#fff;border:1px solid rgba(15,23,42,0.04);display:flex;gap:12px;align-items:center}
    .bm-product-item .info{flex:1}
    .bm-product-item .info strong{display:block;font-size:14px;color:var(--bm-text)}
    .bm-product-item .info small{color:var(--bm-muted);font-size:12px}
    .bm-product-item button{background:transparent;border:1px solid var(--bm-accent-2);color:var(--bm-accent-2);padding:6px 10px;border-radius:8px;cursor:pointer}
    .bm-product-item .price{font-weight:700;color:var(--bm-accent-2)}
    /* scrollbar ligero */
    .bm-chatbot-messages::-webkit-scrollbar{width:8px}
    .bm-chatbot-messages::-webkit-scrollbar-thumb{background:linear-gradient(180deg,rgba(15,23,42,0.12),rgba(15,23,42,0.06));border-radius:8px}
    @media(max-width:420px){.bm-chatbot-panel{right:12px;left:12px;width:auto;height:60vh}}
  `;
  document.head.appendChild(style);

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  // Root
  const root = document.createElement('div');
  document.body.appendChild(root);

  const btn = document.createElement('button');
  btn.className='bm-chatbot-button';
  btn.textContent='💬';
  document.body.appendChild(btn);

  const panel = document.createElement('div');
  panel.className='bm-chatbot-panel';
  panel.style.display='none';
  panel.innerHTML = `
    <div class="bm-chatbot-header">
      <div class="bm-chatbot-brand">
        <div class="bm-chatbot-avatar">BM</div>
        <div>
          <div class="bm-chatbot-title">Asistente BiomeMarket</div>
          <div class="bm-chatbot-sub">Ayuda rápida para tus compras</div>
        </div>
      </div>
      <div class="bm-chatbot-actions">
        <button id="bm-close-panel" aria-label="Cerrar">✕</button>
      </div>
    </div>
    <div class="bm-chatbot-messages" id="bm-messages"></div>
    <!-- Opciones ahora presentadas como lista en el chat; mantenemos input visible para modo listado -->
    <div class="bm-chatbot-input" style="display:flex">
      <input id="bm-input" placeholder="Escribe el número o tu opción..."> 
      <button id="bm-send">Enviar</button>
    </div>
  `;
  document.body.appendChild(panel);

  const messages = panel.querySelector('#bm-messages');
  const input = panel.querySelector('#bm-input');
  const send = panel.querySelector('#bm-send');
  const optionsContainer = panel.querySelector('#bm-options');
  const optBrowse = panel.querySelector('#bm-opt-browse');
  const optPopular = panel.querySelector('#bm-opt-popular');
  const optOffers = panel.querySelector('#bm-opt-offers');
  const optCartSmall = panel.querySelector('#bm-opt-cart-small');

  btn.addEventListener('click', ()=>{
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
  });

  function appendMessage(text, who='bot'){ 
    const div = document.createElement('div');
      div.className = 'bm-msg '+who;
      const bubble = document.createElement('div');
      bubble.className='bubble';
      // allow simple HTML (like small tags) for emphasis if needed
      bubble.innerHTML = text;
      div.appendChild(bubble);
      // meta (timestamp)
      const meta = document.createElement('div');
      meta.className = 'meta';
      const now = new Date();
      meta.textContent = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      bubble.appendChild(meta);
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
  }

    function showAuthRequired(){
      // Si ya mostramos el prompt recientemente, evitar duplicados
      const existing = messages.querySelector('.bm-auth-prompt');
      if(existing) return;
      const wrapper = document.createElement('div');
      wrapper.className = 'bm-auth-prompt';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.innerHTML = 'Para usar esta función debes <strong>iniciar sesión</strong> o <strong>registrarte</strong>.';
      const authActions = document.createElement('div');
      authActions.className = 'bm-auth-actions';
      const loginBtn = document.createElement('button');
      loginBtn.className = 'bm-auth-btn primary';
      loginBtn.textContent = 'Iniciar sesión';
      loginBtn.addEventListener('click', ()=>{ window.location.href = '/accounts/signin/'; });
      const signupBtn = document.createElement('button');
      signupBtn.className = 'bm-auth-btn secondary';
      signupBtn.textContent = 'Registrarse';
      signupBtn.addEventListener('click', ()=>{ window.location.href = '/accounts/signup/'; });
      authActions.appendChild(loginBtn);
      authActions.appendChild(signupBtn);
      bubble.appendChild(authActions);
      wrapper.appendChild(bubble);
      messages.appendChild(wrapper);
      messages.scrollTop = messages.scrollHeight;
    }

  function renderProductos(productos){
    if(!productos || productos.length===0){ appendMessage('No encontré productos.', 'bot'); return; }
    productos.forEach(p=>{
      const el = document.createElement('div');
      el.className='bm-product-item';
      el.innerHTML = `<div class="info"><strong>${p.nombre}</strong><small>Precio: $${p.precio} • Stock: ${p.stock} • id:${p.id}</small></div><div style="text-align:right"><div class="price">$${p.precio}</div></div>`;
      const btnAdd = document.createElement('button');
      btnAdd.textContent='Ver';
      btnAdd.addEventListener('click', ()=>{
        // redirigir al detalle del producto si existe ruta
        window.location.href = `/detalle_producto/${p.id}/`;
      });
      el.appendChild(btnAdd);
      messages.appendChild(el);
    });
    messages.scrollTop = messages.scrollHeight;
  }

  function normalize(text){ return (text||'').toString().trim().toLowerCase(); }

  function handleChoiceOrMessage(raw){
    const msg = (raw||'').toString().trim();
    if(!msg) return;
    // mostrar lo que el usuario escribió
    appendMessage(msg, 'user');
    // intentar interpretar como elección localmente (número o texto clave)
    const n = msg.match(/^\s*(\d+)\s*$/);
    const lower = normalize(msg);
    // mapa de opciones: 1=buscar,2=populares,3=ofertas,4=carrito
    if(n){
      const val = parseInt(n[1],10);
      if(val===1){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('buscar productos', {dontAppendUser:true}); return; }
      if(val===2){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('productos populares', {dontAppendUser:true}); return; }
      if(val===3){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('mostrar ofertas', {dontAppendUser:true}); return; }
      if(val===4){ if(!isAuthenticated()){ showAuthRequired(); return; } window.location.href='/carrito/'; return; }
    }
    // texto libre: buscar palabras claves
    if(lower.includes('buscar') || lower.includes('buscar productos') || lower.includes('buscar producto')){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('buscar productos', {dontAppendUser:true}); return; }
    if(lower.includes('popular')){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('productos populares', {dontAppendUser:true}); return; }
    if(lower.includes('oferta')){ if(!isAuthenticated()){ showAuthRequired(); return; } sendMessage('mostrar ofertas', {dontAppendUser:true}); return; }
    if(lower.includes('carrit')){ if(!isAuthenticated()){ showAuthRequired(); return; } window.location.href='/carrito/'; return; }
    // si no coincide con ninguna opción conocida, enviar al backend como mensaje libre
    sendMessage(msg, {dontAppendUser:true});
  }

  async function sendMessage(msg, opts){
    opts = opts || {};
    if(!msg || !msg.trim()) return;
    if(!opts.dontAppendUser){ appendMessage(msg, 'user'); }
    input.value='';
    try{
      const csrftoken = getCookie('csrftoken');
      const res = await fetch('/chatbot/api/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({message: msg})
      });
      const data = await res.json();
      if(data.type === 'productos'){
        renderProductos(data.productos);
      } else if(data.type === 'carrito'){
        if(data.items.length===0) appendMessage('Tu carrito está vacío.', 'bot');
        else{
          data.items.forEach(it=>{
            appendMessage(`${it.nombre} x${it.cantidad} — $${it.subtotal}`, 'bot');
          });
          appendMessage(`Total: $${data.total}`, 'bot');
        }
      } else if(data.type === 'texto'){
        appendMessage(data.message, 'bot');
      } else {
        appendMessage(JSON.stringify(data), 'bot');
      }
    }catch(err){
      appendMessage('Error de conexión con el servidor.', 'bot');
      console.error(err);
    }
  }

  if(send){ send.addEventListener('click', ()=>handleChoiceOrMessage(input ? input.value : '')); }
  if(input){ input.addEventListener('keydown',(e)=>{ if(e.key==='Enter'){ handleChoiceOrMessage(input.value); } }); }

  // botón cerrar panel (header)
  const closeBtn = panel.querySelector('#bm-close-panel');
  if(closeBtn){
    closeBtn.addEventListener('click', ()=>{ panel.style.display = 'none'; });
  }

  // Opciones rápidas (botones) con verificación de autenticación
  function isAuthenticated(){ try{ return Boolean(window.BM_USER && window.BM_USER.authenticated); }catch(e){ return false; } }

  if(optBrowse){
    optBrowse.addEventListener('click', ()=>{
      if(!isAuthenticated()){ showAuthRequired(); return; }
      sendMessage('buscar productos');
    });
  }
  if(optPopular){
    optPopular.addEventListener('click', ()=>{
      if(!isAuthenticated()){ showAuthRequired(); return; }
      sendMessage('productos populares');
    });
  }
  if(optOffers){
    optOffers.addEventListener('click', ()=>{
      if(!isAuthenticated()){ showAuthRequired(); return; }
      sendMessage('mostrar ofertas');
    });
  }
  if(optCartSmall){
    optCartSmall.addEventListener('click', ()=>{
      if(!isAuthenticated()){ showAuthRequired(); return; }
      try{ window.location.href = '/carrito/'; }catch(e){ sendMessage('ver mi carrito'); }
    });
  }

  // (Se eliminó el botón 'Carrito' del header; la acción para abrir carrito se mantiene en las opciones inferiores)

  // Mensaje inicial: listar opciones numeradas para que el usuario escriba su elección
  appendMessage('¡Hola! Bienvenido a BiomeMarket — elige una opción para comenzar:<br><br>1) Buscar productos<br>2) Populares<br>3) Ofertas<br>4) Ver carrito<br><br>Escribe el número de la opción o escribe el nombre (ej. "1" o "buscar").', 'bot');

})();
