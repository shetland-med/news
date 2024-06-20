document.addEventListener('DOMContentLoaded', function () {
    var newsDataElement = document.getElementById('news-data');
    var appsDataElement = document.getElementById('apps-data');

    if (newsDataElement && appsDataElement) {
        var newsData = JSON.parse(newsDataElement.textContent);
        var appsData = JSON.parse(appsDataElement.textContent);

        new Vue({
            el: '#app',
            delimiters: ['${', '}'], // Vue.jsのデリミタを変更
            data: {
                appsData: appsData,
                selectedNews: newsData.map(news => ({ 
                    original: { ...news }, // 元のデータを保存
                    current: { ...news }, // 編集可能なデータ
                    changed: false, 
                    changedCells: [], 
                    file: null,
                    newRow: false // 新規追加された行かどうかのフラグ
                })),
                displayedNews: [], // 表示するニュースのリスト
                selectedApps: [],
                showModal: false,
                displayApps: "",
                isTestMode: true,
            },
            created() {
                this.displayedNews = [...this.selectedNews];
                this.$nextTick(() => {
                    flatpickr(".flatpickr", {
                        dateFormat: "Y-m-d"
                    });
                });
            },
            mounted(){
                this.initializeFlatpickr();
            },
            computed:{
                filteredNews(){
                    return this.displayedNews.filter(news => this.isTestMode || (!this.isTestMode && news.current[6] != ""));
                }
            },
            methods: {
                getFileName(path) {
                    if (!path) return '';
                    try {
                        // Decode URI components to handle encoded characters
                        const decodedPath = decodeURIComponent(path);
                        // Split by "/" and return the last part
                        return decodedPath.split('/').pop();
                    } catch (error) {
                        console.error('Error decoding file path:', error);
                        return '';
                    }
                },
                fileChanged(event, news) {
                    const file = event.target.files[0];
                    news.current[9] = file.name;
                    news.file = file;
                    this.$set(news, 'fileUrl', URL.createObjectURL(file)); 
                    this.markChanged(news, 9);
                },                
                initializeFlatpickr() {
                    this.$nextTick(() => {
                        flatpickr(".flatpickr", {
                            locale: 'ja'
                        });
                    });
                },
                toggleMode() {
                    this.isTestMode = !this.isTestMode;
                    this.initializeFlatpickr();
                },
                toggleModal() {
                    this.showModal = !this.showModal;
                },
                redirectToNews() {
                    if (this.isTestMode) {
                        window.location.href = '/news/test';
                    }
                    else {
                        window.location.href = '/news/honban';
                    }
                    
                },
                cancelSearch() {
                    this.showModal = false;
                },
                applyFilter() {
                    this.showModal = false;
                    if (this.selectedApps.length === 0) {
                        this.displayedNews = [...this.selectedNews];
                    } else {
                        this.displayedNews = this.selectedNews.filter(news => this.selectedApps.includes(news.current[0]));
                    }
                    this.displayApps = this.selectedApps.join(', ');
                },
                addRow() {
                    const newRow = {
                        original: {
                            0: '',//アプリカテゴリ
                            1: '',//カテゴリ
                            2: '',//タイトル
                            3: '',//公開年度
                            4: '',//公開日
                            5: '14',//公開期間
                            6: '',//ニュースファイル名
                            7: 0,//掲載終了フラグ
                            8: '',//ニュースID
                            9: '',//古いニュースファイル名
                            10: ''//ステータス
                        },
                        current: {
                            0: '',//アプリカテゴリ
                            1: '',//カテゴリ
                            2: '',//タイトル
                            3: '',//公開年度
                            4: '',//公開日
                            5: '14',//公開期間
                            6: '',//ニュースファイル名
                            7: 0,//掲載終了フラグ
                            8: '',//ニュースID
                            9: '',//古いニュースファイル名
                            10: ''//ステータス
                        },
                        changed: true,
                        changedCells: [],
                        file: null,
                        newRow: true // 新規追加された行
                    };
                    this.selectedNews.push(newRow);
                    this.displayedNews.push(newRow);
                },
                deleteRow(news) {
                    const index = this.selectedNews.indexOf(news);
                    if (index > -1) {
                        this.selectedNews.splice(index, 1);
                        this.displayedNews.splice(this.displayedNews.indexOf(news), 1);
                    }
                },
                markChanged(news, cellIndex, event = null) {
                    if (cellIndex === 4){
                        let year = news.current[4].substring(0, 4); //上4桁を切り取る
                        news.current[3] = year;                     //news.current[3]（公開年度）に設定する
                    }
                    if (news.newRow) {
                        if (cellIndex === 6 && event) {
                            const file = event.target.files[0];
                            news.file = file;
                            news.current[cellIndex] = file.name;
                        }
                        return; // 新規追加された行は変更マークを付けない
                    }

                    let newValue = news.current[cellIndex];
                    let originalValue = news.original[cellIndex];

                    if (cellIndex === 9 && event) {
                        const file = event.target.files[0];
                        news.file = file;
                        newValue = file.name;
                    } else if (cellIndex === 7) {
                        newValue = news.current[7] ? 1 : 0;
                    }

                    if (String(newValue) !== String(originalValue)) {
                        if (!news.changedCells.includes(cellIndex)) {
                            news.changedCells.push(cellIndex);
                        }
                        news.current[cellIndex] = newValue;
                        news.changed = true;
                    } else {
                        news.changedCells = news.changedCells.filter(index => index !== cellIndex);
                        news.current[cellIndex] = newValue;
                        if (news.changedCells.length === 0) {
                            news.changed = false;
                        }
                    }

                    // Check if all cells are back to original values, if so, reset changed state
                    if (news.changed && Object.keys(news.current).every(key => news.current[key] === news.original[key])) {
                        news.changed = false;
                    }
                },
                resetValue(news) {
                    news.current = JSON.parse(JSON.stringify(news.original));
                    news.changed = false;
                    news.changedCells = [];
                },
                calculateEndDate(startDate, period) {
                    if (!startDate || !period) return '';
                    const start = new Date(startDate);
                    const end = new Date(start);
                    end.setDate(start.getDate() + parseInt(period));
                    return end.toISOString().split('T')[0];
                },
                checkFormat() {
                    // フォーマットチェック
                    // index:5(掲載期間)
                    var alertMessage = "";
                    var count = 0;
                    for (let news of this.selectedNews) {
                        count++;
                        Object.values(news.current).forEach((value, index) => {
                            if (index == 5) {
                                // value[5]が数字かチェック
                                if (!/^\d+$/.test(value)) {
                                    alertMessage += count + "行目:公開期間は半角数字を入力してください。\n";
                                }
                            }
                        });
                    }
                    return alertMessage
                },
                registerChanges() {
                    const changedNews = this.selectedNews.filter(news => news.changed);
                    const formData = new FormData();

                    if (changedNews == ""){
                        return
                    }
                    // 必須項目チェック
                    // index:6(本番用ニュースファイル)、7(掲載終了フラグ)、8(News_ID)、9(確認終了フラグ)、10(ステータス)
                    for (let news of changedNews) {
                        if (Object.values(news.current).some((value, index) =>index !== 6 && index !== 7 && index !== 8 && index !== 9 && index !== 10 && !value)) {
                            alert('すべての必須項目を入力してください。');
                            return;
                        }
                    }
                    
                    var alertMessage = this.checkFormat();
                    if (alertMessage != ""){
                        this.displayedNews = [...this.selectedNews]
                        setTimeout(() => {
                            alert(alertMessage);
                        }, 100);
                        return
                    }

                    changedNews.forEach((news, index) => {
                        if (news.file) {
                            formData.append(`file_${index}`, news.file, news.file.name);
                        }
                        formData.append(`news_${index}`, JSON.stringify({current:news.current, newRow: news.newRow}));
                    });

                    axios.post('/register', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    })
                    .then(response => {
                        if (response.data.status === 'success') {
                            alert('登録に成功しました');
                            this.selectedNews.forEach(news => {
                                if (news.changed) {
                                    news.original = { ...news.current };
                                    news.changed = false;
                                    news.changedCells = [];
                                    news.newRow = false; // 新規追加行のフラグをリセット
                                }
                            });
                            this.applyFilter(); // フィルターを再適用
                        } else {
                            alert('登録に失敗しました: ');
                        }
                    })
                    .catch(error => {
                        alert('登録中にエラーが発生しました: ' + error);
                    })
                    .then(() =>{
                        location.reload();
                    })
                },
                updateProductionFile(news) {
                    if (!news.current[9]) {
                        alert('テスト用ニュースファイルが選択されていません。');
                        return;
                    }
                    else {
                        // テスト用ニュースファイルを本番用ニュースファイルに更新
                        news.current[6] = news.current[9];
                    }
            
                    const formData = new FormData();
                    formData.append('news', JSON.stringify(news.current));
                    if (news.file) {
                        formData.append('file', news.file, news.file.name);
                    }
            
                    axios.post('/update_production', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    })
                    .then(response => {
                        if (response.data.status === 'success') {
                            alert('本番掲載に成功しました');

                        } else {
                            alert('本番掲載に失敗しました: ' + response.data.message);
                        }
                    })
                    .catch(error => {
                        alert('本番掲載中にエラーが発生しました: ' + error);
                    })
                    .then(() =>{
                        location.reload();
                    });
                }
            }
        });
    } else {
        console.error('Required elements are missing.');
    }
});
