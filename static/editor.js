'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const state = {file:null, notes:[], tracks:[], ppq:480, selected:new Set(), history:[], page:0, busy:false};
  const pageSize = 100;
  const pitchNames = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
  const pitchName = pitch => `${pitchNames[pitch % 12]}${Math.floor(pitch / 12) - 1}`;
  const changed = note => note.hand !== note.suggested_hand;
  const number = value => new Intl.NumberFormat().format(value);

  function status(message, kind='') {
    $('status').textContent = message;
    $('status').className = `status ${kind}`;
    $('status').hidden = false;
  }
  function filtered() {
    const query = $('search').value.trim().toLowerCase();
    const hand = $('handFilter').value, track = $('trackFilter').value;
    return state.notes.filter(n => (!query || pitchName(n.pitch).toLowerCase().includes(query) || String(n.pitch) === query) &&
      (!hand || (hand === 'EDITED' ? changed(n) : n.hand === hand)) && (!track || String(n.track) === track));
  }
  function setBusy(value) {
    state.busy = value;
    $('fileInput').disabled = value;
    $('fileButton').classList.toggle('disabled', value);
    $('review').setAttribute('aria-busy', String(value));
    render();
  }
  function cell(text, className='') {
    const td = document.createElement('td');
    td.textContent = text;
    td.className = className;
    return td;
  }
  function render() {
    const matches = filtered();
    const pages = Math.max(1, Math.ceil(matches.length/pageSize));
    state.page = Math.min(state.page, pages-1);
    const visible = matches.slice(state.page*pageSize, (state.page+1)*pageSize);
    const body = $('noteRows');
    body.replaceChildren();
    for (const n of visible) {
      const tr = document.createElement('tr');
      tr.classList.toggle('selected', state.selected.has(n.id));
      const checkCell = document.createElement('td');
      const check = document.createElement('input');
      check.type = 'checkbox'; check.checked = state.selected.has(n.id); check.disabled = state.busy;
      check.dataset.id = n.id; check.setAttribute('aria-label', `Select ${pitchName(n.pitch)} at beat ${(n.start_tick/state.ppq + 1).toFixed(2)}`);
      check.addEventListener('change', () => {check.checked ? state.selected.add(n.id) : state.selected.delete(n.id); render();});
      checkCell.append(check); tr.append(checkCell);
      const name = document.createElement('td'), strong = document.createElement('strong'), sub = document.createElement('span');
      strong.textContent = pitchName(n.pitch);
      if (changed(n)) {const dot = document.createElement('span'); dot.className='edited-indicator'; dot.title='Hand edited'; strong.append(dot);}
      sub.className='secondary'; sub.textContent=`MIDI ${n.pitch}`; name.append(strong, sub); tr.append(name);
      tr.append(cell((n.start_tick/state.ppq+1).toFixed(2)), cell((n.duration_ticks/state.ppq).toFixed(2), 'duration-column'));
      const trackName = state.tracks.find(t=>t.index===n.track)?.name || `Track ${n.track+1}`;
      const trackCell = cell(trackName, 'track-column'); trackCell.title=trackName; tr.append(trackCell);
      const handCell = document.createElement('td'), select = document.createElement('select');
      select.className=`hand-select is-${n.hand.toLowerCase()}`; select.disabled=state.busy;
      select.setAttribute('aria-label', `Hand for ${pitchName(n.pitch)} at beat ${(n.start_tick/state.ppq+1).toFixed(2)}`);
      for (const hand of ['LEFT','RIGHT']) {const o=document.createElement('option'); o.value=hand; o.textContent=hand==='LEFT'?'Left hand':'Right hand'; select.append(o);}
      select.value=n.hand; select.addEventListener('change',()=>applyChanges([n.id], select.value)); handCell.append(select); tr.append(handCell); body.append(tr);
    }
    const total=state.notes.length, edits=state.notes.filter(changed).length;
    $('editCount').textContent=`${number(edits)} ${edits===1?'edit':'edits'}`;
    $('leftCount').textContent=number(state.notes.filter(n=>n.hand==='LEFT').length);
    $('rightCount').textContent=number(state.notes.filter(n=>n.hand==='RIGHT').length);
    $('selectedCount').textContent=`${number(state.selected.size)} selected`;
    $('reviewDetail').textContent=state.file ? `${number(total)} notes · ${number(matches.length)} match your filters` : 'Import a MIDI to get started';
    $('tableRegion').hidden=!matches.length;
    $('empty').hidden=Boolean(matches.length);
    $('emptyHeading').textContent=state.file ? (total?'No matching notes':'No notes in this MIDI') : 'Your notes will appear here';
    $('emptyText').textContent=state.file ? (total?'Try another filter or search.':'Tempo and other events will still be preserved when you export.') : 'Import a MIDI file, review the suggested hands, and make it your own.';
    $('pageInfo').textContent=matches.length ? `${number(state.page*pageSize+1)}–${number(Math.min((state.page+1)*pageSize,matches.length))} of ${number(matches.length)}` : '0 notes';
    $('prevPage').disabled=state.busy || state.page===0; $('nextPage').disabled=state.busy || state.page>=pages-1;
    $('exportButton').disabled=state.busy || !state.file;
    for (const id of ['setLeft','setRight','restoreSelected']) $(id).disabled=state.busy || !state.selected.size;
    $('clearSelection').disabled=state.busy || !state.selected.size;
    $('selectMatching').disabled=state.busy || !matches.length;
    $('undo').disabled=state.busy || !state.history.length;
    const count=visible.filter(n=>state.selected.has(n.id)).length;
    $('selectPage').checked=Boolean(visible.length && count===visible.length);
    $('selectPage').indeterminate=count>0 && count<visible.length;
    $('selectPage').disabled=state.busy || !visible.length;
    for (const id of ['search','handFilter','trackFilter']) $(id).disabled=state.busy;
  }
  function applyChanges(ids, hand) {
    if (state.busy) return;
    const wanted=new Set(ids), changes=[];
    for (const n of state.notes) if(wanted.has(n.id)) {const next=hand==='RESTORE'?n.suggested_hand:hand; if(next!==n.hand){changes.push({id:n.id, before:n.hand}); n.hand=next;}}
    if(changes.length){state.history.push(changes); if(state.history.length>50)state.history.shift();}
    render();
  }
  async function checkResponse(response) {
    if(!response.ok){let message='The file could not be processed. Please try again.'; try{message=(await response.json()).error||message;}catch{} throw new Error(message);}
    return response;
  }
  async function importFile(file) {
    if(!file || state.busy)return;
    if(!/\.(mid|midi)$/i.test(file.name)){status('Choose a .mid or .midi file.', 'error'); return;}
    if(file.size>16*1024*1024){status('Choose a MIDI smaller than 16 MB.', 'error'); return;}
    setBusy(true); status('Reading your MIDI and suggesting hands…', 'busy');
    try{
      const data=new FormData(); data.append('midi',file);
      const response=await checkResponse(await fetch('/api/analyze',{method:'POST',body:data}));
      const result=await response.json();
      state.file=file; state.notes=result.notes; state.tracks=result.tracks; state.ppq=result.ticks_per_beat;
      state.selected.clear(); state.history=[]; state.page=0;
      $('search').value=''; $('handFilter').value=''; $('trackFilter').replaceChildren(new Option('All tracks',''));
      for(const track of state.tracks)$('trackFilter').append(new Option(track.name,String(track.index)));
      $('fileName').textContent=file.name;
      $('fileDetail').textContent=`${number(result.note_count)} notes · ${number(result.tracks.length)} ${result.tracks.length===1?'track':'tracks'}`;
      status('Ready to review. Change a note’s hand, or select a group and assign it together.', 'success');
    }catch(error){status(error.message, 'error');}
    finally{setBusy(false); $('fileInput').value='';}
  }
  $('fileInput').addEventListener('change', event=>importFile(event.target.files[0]));
  const zone=$('dropzone');
  for(const kind of ['dragenter','dragover'])zone.addEventListener(kind,event=>{event.preventDefault(); if(!state.busy)zone.classList.add('dragging');});
  for(const kind of ['dragleave','drop'])zone.addEventListener(kind,event=>{event.preventDefault();zone.classList.remove('dragging');});
  zone.addEventListener('drop',event=>importFile(event.dataTransfer.files[0]));
  for(const id of ['search','handFilter','trackFilter'])$(id).addEventListener(id==='search'?'input':'change',()=>{state.page=0;render();});
  $('selectPage').addEventListener('change', event=>{for(const n of filtered().slice(state.page*pageSize,(state.page+1)*pageSize))event.target.checked?state.selected.add(n.id):state.selected.delete(n.id);render();});
  $('selectMatching').addEventListener('click',()=>{for(const n of filtered())state.selected.add(n.id);render();});
  $('clearSelection').addEventListener('click',()=>{state.selected.clear();render();});
  $('setLeft').addEventListener('click',()=>applyChanges(state.selected,'LEFT'));
  $('setRight').addEventListener('click',()=>applyChanges(state.selected,'RIGHT'));
  $('restoreSelected').addEventListener('click',()=>applyChanges(state.selected,'RESTORE'));
  $('undo').addEventListener('click',()=>{const changes=state.history.pop();if(changes){const map=new Map(changes.map(c=>[c.id,c.before]));for(const n of state.notes)if(map.has(n.id))n.hand=map.get(n.id);render();}});
  $('prevPage').addEventListener('click',()=>{state.page--;render();}); $('nextPage').addEventListener('click',()=>{state.page++;render();});
  $('exportButton').addEventListener('click',async()=>{
    if(!state.file || state.busy)return;
    setBusy(true);status('Checking timing and events before export…','busy');
    try{
      const data=new FormData();data.append('midi',state.file);data.append('assignments',JSON.stringify(Object.fromEntries(state.notes.map(n=>[n.id,n.hand]))));
      const response=await checkResponse(await fetch('/api/export',{method:'POST',body:data}));
      const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');
      a.href=url;a.download=state.file.name.replace(/\.(mid|midi)$/i,'')+'-hands.mid';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
      status('MIDI checks passed. Your corrected file is ready in downloads.','success');
    }catch(error){status(error.message,'error');}finally{setBusy(false);}
  });
  render();
})();
