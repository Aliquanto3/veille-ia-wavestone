document.addEventListener('DOMContentLoaded', () => {
                const filterHeader = document.querySelector('.filters-header');
                const filterPanel = document.querySelector('.filters-panel');
                if(filterHeader) filterHeader.addEventListener('click', () => { filterPanel.classList.toggle('open'); });

                document.querySelectorAll('.news-title').forEach(header => {
                    header.addEventListener('click', () => { header.parentElement.classList.toggle('active'); });
                });

                document.querySelectorAll('.copy-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const item = btn.closest('.news-item');
                        const title = item.querySelector('.news-title span').innerText;
                        const desc = item.querySelector('.news-description-text').innerText.trim();
                        const links = [];
                        item.querySelectorAll('.links a').forEach(a => links.push(a.href));
                        
                        let textToCopy = `**${title}**\\n\\n${desc}`;
                        if(links.length > 0) textToCopy += `\\n\\n**Sources :**\\n` + links.map(l => `- ${l}`).join('\\n');

                        navigator.clipboard.writeText(textToCopy).then(() => {
                            const originalText = btn.innerText;
                            btn.innerText = "✅ Copié !";
                            btn.style.backgroundColor = "var(--accent)";
                            btn.style.borderColor = "var(--accent)";
                            btn.style.color = "black";
                            setTimeout(() => {
                                btn.innerText = originalText;
                                btn.style.backgroundColor = ""; btn.style.borderColor = ""; btn.style.color = "";
                            }, 2000);
                        }).catch(err => { alert("Erreur copie."); });
                    });
                });

                const searchInput = document.getElementById('searchInput');
                const dateStartInput = document.getElementById('dateStart');
                const dateEndInput = document.getElementById('dateEnd');
                const resetDatesBtn = document.getElementById('resetDates');
                const catCheckboxes = document.querySelectorAll('.cat-cb');
                const subCheckboxes = document.querySelectorAll('.sub-cb');
                const columns = document.querySelectorAll('.column');
                const items = document.querySelectorAll('.news-item');

                function updateFilters() {
                    const searchTerm = searchInput.value.toLowerCase();
                    const selectedCats = Array.from(catCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
                    const selectedSubs = Array.from(subCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
                    const dateStart = dateStartInput ? dateStartInput.value : '';
                    const dateEnd = dateEndInput ? dateEndInput.value : '';

                    columns.forEach(col => {
                        const cat = col.dataset.cat;
                        if (selectedCats.length === 0 || selectedCats.includes(cat)) col.style.display = 'flex';
                        else col.style.display = 'none';
                    });

                    items.forEach(item => {
                        const title = item.querySelector('.news-title').innerText.toLowerCase();
                        const desc = item.querySelector('.news-content').innerText.toLowerCase();
                        const itemCat = item.dataset.cat;
                        const itemSub = item.dataset.sub;
                        const itemDate = item.dataset.date || '';
                        const matchesSearch = title.includes(searchTerm) || desc.includes(searchTerm);
                        const matchesCat = selectedCats.length === 0 || selectedCats.includes(itemCat);
                        const matchesSub = selectedSubs.length === 0 || selectedSubs.includes(itemSub);
                        const matchesDateStart = !dateStart || itemDate >= dateStart;
                        const matchesDateEnd = !dateEnd || itemDate <= dateEnd;
                        item.style.display = (matchesSearch && matchesCat && matchesSub && matchesDateStart && matchesDateEnd) ? 'block' : 'none';
                    });
                    
                    document.querySelectorAll('.sub-group').forEach(group => {
                        const visibleChildren = Array.from(group.querySelectorAll('.news-item')).filter(i => i.style.display !== 'none');
                        const header = group.querySelector('.sub-header');
                        if (header) header.style.display = visibleChildren.length > 0 ? 'flex' : 'none';
                    });
                }

                document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.addEventListener('change', (e) => {
                        const label = e.target.parentElement;
                        if(e.target.checked) label.classList.add('checked');
                        else label.classList.remove('checked');
                        updateFilters();
                    });
                });
                searchInput.addEventListener('input', updateFilters);
                if(dateStartInput) dateStartInput.addEventListener('change', updateFilters);
                if(dateEndInput) dateEndInput.addEventListener('change', updateFilters);
                if(resetDatesBtn) resetDatesBtn.addEventListener('click', () => {
                    dateStartInput.value = '';
                    dateEndInput.value = '';
                    updateFilters();
                });
            });