document.addEventListener('DOMContentLoaded', function () {
    var newsDataElement = document.getElementById('news-data');
    var newsData = JSON.parse(newsDataElement.textContent);
    var appsDataElement = document.getElementById('app-data');
    var appsData = JSON.parse(appsDataElement.textContent);
    var previous_newsDataElement = document.getElementById('previous-data');
    var previous_newsData = JSON.parse(previous_newsDataElement.textContent);
    var filtered_appsDataElement = document.getElementById('filter-apps');
    var filtered_appsData = JSON.parse(filtered_appsDataElement.textContent);


    new Vue({
        el: '#app',
        delimiters: ['${', '}'],//Vue.jsのデリミタを変更
        data: {
            newsData: newsData,
            appsData: appsData,
            previous_newsData: previous_newsData,
            filtered_appsData: filtered_appsData,
            selectedNews: [],
            selectedApps: [],
            showModal: false,
            displayApps: "",
            categories: [],
            years: []
        },
        created() {
            this.updateCategoryCounts();
            this.updateYearCounts();
            //日付順に並び替え
            this.sortByDate(this.previous_newsData);
            this.sortByDate(this.newsData);
            this.selectedNews = [...this.previous_newsData];
            this.selectedApps = [...this.filtered_appsData];
            this.displayApps = [...this.selectedApps].join(',');
        },
        methods: {
            //カテゴリ別に件数をカウント
            updateCategoryCounts() {
                var categories = new Set(this.newsData.map(news => news[3]));
                this.categories = Array.from(categories).map(category => ({
                    name: category,
                    count: this.newsData.filter(news => news[3] === category).length
                }));
            },
            //年度別に件数をカウント
            updateYearCounts() {
                var years = new Set(this.previous_newsData.map(news => news[6]));
                this.years = Array.from(years).map(year => ({
                    year: year,
                    count: this.previous_newsData.filter(news => news[6] === year).length
                })).sort((a, b) => b.year - a.year);
            },
            //カテゴリをクリックした際に関連するニュースを一覧に表示する処理
            selectCategory(category) {
                this.selectedNews = this.newsData.filter(news => news[3] === category);
            },
            //年度をクリックした際に関連するニュースを一覧に表示する処理
            selectYear(year) {
                this.selectedNews = this.previous_newsData.filter(news => news[6] === year);
            },
            //日付順に並び替え
            sortByDate(data) {
                data.sort((a, b) => {
                    const dateA = new Date(a[5].split('-').map(num => num.padStart(2, '0')).join('-'));
                    const dateB = new Date(b[5].split('-').map(num => num.padStart(2, '0')).join('-'));
                    return dateB - dateA;
                });
            },
            //フィルタ検索処理
            searchNewsByApps() {
                const data = JSON.stringify(this.selectedApps);
                fetch('http://localhost:5000/search', {
                    method: 'POST',
                    headers: {
                        "Content-Type": 'application/json',
                    },
                    body: data,
                })
                .then(response => response.json())
                .then(data => {
                    //データプロパティを更新
                    this.newsData = data.filtered_new_data;
                    this.appsData = data.filtered_apps;
                    this.previous_newsData = data.filtered_previous_data;
                    this.selectedNews = data.filtered_previous_data;
                    //更新したデータを日付順に並び替え
                    this.sortByDate(this.newsData);
                    this.sortByDate(this.previous_newsData);
                    this.sortByDate(this.selectedNews);
                    this.updateCategoryCounts();
                    this.updateYearCounts();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
                this.showModal = false;
                this.displayApps = this.selectedApps.join(', ');
            },
            //フィルタ用ポップアップの非表示処理
            toggleModal() {
                this.showModal = !this.showModal;
            },
            //フィルタ用ポップアップのキャンセルボタン押下時の処理
            cancelSearch() {
                this.showModal = false;
            }
        }
    });
});

