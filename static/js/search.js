console.log("search_scripts.js loaded"); 
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-query');
    const liveResultsContainer = document.getElementById('search-results-live');
    const searchForm = document.getElementById('search-form'); // Assuming your form has this ID
    const productSearchApiUrl = searchInput ? searchInput.dataset.searchUrl : null; // Get URL from data attribute
    let searchTimeout;

    if (searchInput && liveResultsContainer && productSearchApiUrl) {
        searchInput.addEventListener('keyup', function (e) {
            const query = e.target.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                liveResultsContainer.innerHTML = '';
                liveResultsContainer.style.display = 'none';
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`${productSearchApiUrl}?q=${encodeURIComponent(query)}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        liveResultsContainer.innerHTML = ''; 
                        if (data.products && data.products.length > 0) {
                            liveResultsContainer.style.display = 'block';
                            data.products.slice(0, 5).forEach(product => {
                                const a = document.createElement('a');
                                a.href = product.detail_url; 
                                a.classList.add('search-list-group-item', 'justify-center');
                                
                                let content = `<div class="search-cart flex w-full justify-content">
                                                <div class="search-title justify-content">
                                                 <h6 class="m-0 text-sm">${product.name}</h6>`;

                                if (product.category_name) {
                                    content += `<small class="text-gray-500">در دسته بندی: ${product.category_name}</small>`;
                                }

                                content += `</div>`;
                                if(product.price){
                                    if (parseInt(product.price) == parseInt(product.discounted_price)){
                                        content += `<p class="search-text-price">
                                                        <span class="text-primary font-bold">${parseInt(product.price)} تومان</span>
                                                    </p>`;
                                    }else if (parseInt(product.price) > parseInt(product.discounted_price)){
                                        content += `<p class="search-text-price">
                                                        <span class="text-primary-red text-decoration-line-through">${parseInt(product.price)} تومان</span></br>
                                                        <span class="text-primary font-bold">${parseInt(product.discounted_price)} تومان</span>
                                                    </p>`;
                                    }
                                }
                                content += `</div>`;
                                a.innerHTML = content;
                                const div = document.createElement('div');
                                div.classList.add('hover:bg-gray-100')
                                div.appendChild(a);
                                liveResultsContainer.appendChild(div);
                            });
                        } else {
                            liveResultsContainer.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching live search results:', error);
                        liveResultsContainer.innerHTML = '<li class="list-group-item text-danger">خطا در جستجو</li>';
                        liveResultsContainer.style.display = 'block';
                    });
            }, 300); 
        });

        // Hide live results when clicking outside the search form or results container
        document.addEventListener('click', function(event) {
            if (liveResultsContainer.style.display !== 'none') {
                const isClickInsideSearchForm = searchForm ? searchForm.contains(event.target) : false;
                const isClickInsideResults = liveResultsContainer.contains(event.target);
                if (!isClickInsideSearchForm && !isClickInsideResults) {
                    liveResultsContainer.style.display = 'none';
                }
            }
        });
    } else {
        if (!searchInput) console.log('Search input not found');
        if (!liveResultsContainer) console.log('Live results container not found');
        if (!productSearchApiUrl && searchInput) console.log('Search API URL data attribute not found on search input');
    }
}); 