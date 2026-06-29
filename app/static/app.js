// Usage data component (paid-only + redemption code logic)
function usageData() {
    return {
        usage: { used: 0, global_limit: 100, date: '', price: '19.9', wechat: 'rayz1000' },

        // Redemption code state
        redeemInput: '',
        redeemLoading: false,
        redeemMessage: '',
        redeemSuccess: null,

        // Paid credits state (from localStorage)
        paidCredits: 0,

        // Copy WeChat ID state
        copySuccess: false,

        init() {
            this.fetchUsage();
            this.loadPaidCredits();
        },

        loadPaidCredits() {
            const stored = localStorage.getItem('gaokao_paid_credits');
            this.paidCredits = stored ? parseInt(stored, 10) : 0;
        },

        savePaidCredits() {
            localStorage.setItem('gaokao_paid_credits', String(this.paidCredits));
        },

        async fetchUsage() {
            try {
                const resp = await fetch('/api/v1/usage');
                if (resp.ok) {
                    this.usage = await resp.json();
                }
            } catch (e) {
                console.warn('Failed to fetch usage:', e);
            }
        },

        async submitRedeem() {
            if (!this.redeemInput || this.redeemInput.trim() === '') {
                this.redeemMessage = '请输入兑换码';
                this.redeemSuccess = false;
                return;
            }

            this.redeemLoading = true;
            this.redeemMessage = '';
            this.redeemSuccess = null;

            try {
                const resp = await fetch('/api/v1/redeem', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: this.redeemInput.trim() })
                });

                const data = await resp.json();

                if (data.success) {
                    this.paidCredits += data.credits;
                    this.savePaidCredits();
                    this.redeemMessage = data.message;
                    this.redeemSuccess = true;
                    this.redeemInput = '';
                } else {
                    this.redeemMessage = data.message;
                    this.redeemSuccess = false;
                }
            } catch (e) {
                this.redeemMessage = '兑换请求失败，请稍后重试';
                this.redeemSuccess = false;
            } finally {
                this.redeemLoading = false;
            }
        },

        // Copy WeChat ID to clipboard
        copyWechatId() {
            const wechatId = this.usage.wechat || 'rayz1000';
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(wechatId).then(() => {
                    this.copySuccess = true;
                    setTimeout(() => { this.copySuccess = false; }, 2000);
                }).catch(() => {
                    this._fallbackCopy(wechatId);
                });
            } else {
                this._fallbackCopy(wechatId);
            }
        },

        _fallbackCopy(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.copySuccess = true;
            setTimeout(() => { this.copySuccess = false; }, 2000);
        },

        // Called after a successful analysis — decrement paid credits
        consumeCredit() {
            if (this.paidCredits > 0) {
                this.paidCredits -= 1;
                this.savePaidCredits();
            }
        },

        // Check if user can submit analysis (must have paid credits)
        canAnalyze() {
            return this.paidCredits > 0;
        }
    };
}

// Alpine.js data component for form handling
function formData() {
    return {
        // Form data
        student: {
            name: '',
            province: '',
            score: 0,
            rank: null,
            year: 2026,
            subject_type: '',
            subjectsStr: ''
        },
        family: {
            economic_level: '一般',
            location_pref: '',
            has_abroad_plan: false,
            industryStr: ''
        },
        interestsStr: '',
        careerGoalsStr: '',
        constraintsStr: '',

        // UI state
        loading: false,
        report: null,
        error: null,

        // Progress state
        progress: 0,
        progressMessage: '',
        progressStep: 0,
        totalSteps: 3,

        // Province list
        provinces: [
            '北京', '天津', '上海', '重庆',
            '河北', '山西', '辽宁', '吉林', '黑龙江',
            '江苏', '浙江', '安徽', '福建', '江西', '山东',
            '河南', '湖北', '湖南', '广东', '海南',
            '四川', '贵州', '云南', '陕西', '甘肃', '青海',
            '台湾', '内蒙古', '广西', '西藏', '宁夏', '新疆',
            '香港', '澳门'
        ],

        // Initialize
        init() {
            console.log('College application tool initialized');
        },

        // Parse comma-separated string to array
        parseArray(str) {
            if (!str || str.trim() === '') return [];
            return str.split(',').map(item => item.trim()).filter(item => item !== '');
        },

        // Build request payload
        buildPayload() {
            return {
                student_profile: {
                    student: {
                        name: this.student.name || '匿名',
                        province: this.student.province,
                        score: parseInt(this.student.score) || 0,
                        rank: this.student.rank ? parseInt(this.student.rank) : null,
                        subjects: this.parseArray(this.student.subjectsStr),
                        subject_type: this.student.subject_type,
                        year: parseInt(this.student.year) || 2026
                    },
                    family: {
                        economic_level: this.family.economic_level,
                        location_pref: this.family.location_pref || null,
                        has_abroad_plan: this.family.has_abroad_plan,
                        industry_connections: this.parseArray(this.family.industryStr)
                    },
                    interests: this.parseArray(this.interestsStr),
                    career_goals: this.parseArray(this.careerGoalsStr),
                    constraints: this.parseArray(this.constraintsStr)
                },
                report_type: "full"
            };
        },

        // Validate form
        validateForm() {
            if (!this.student.province) {
                this.error = '请选择省份';
                return false;
            }
            if (!this.student.score || this.student.score < 0 || this.student.score > 750) {
                this.error = '请输入有效的高考分数（0-750）';
                return false;
            }
            if (!this.student.subject_type) {
                this.error = '请选择科类';
                return false;
            }

            // Check paid credits — must have at least 1 credit
            const paidCredits = parseInt(localStorage.getItem('gaokao_paid_credits') || '0', 10);
            if (paidCredits <= 0) {
                this.error = '请先兑换码获取分析次数（分析服务 19.9元/次）';
                return false;
            }

            this.error = null;
            return true;
        },

        // Submit form with progress updates
        async submitForm() {
            if (!this.validateForm()) return;

            this.loading = true;
            this.report = null;
            this.error = null;
            this.progress = 0;
            this.progressMessage = '正在初始化...';
            this.progressStep = 0;

            // Read paid credits for header
            const paidCredits = parseInt(localStorage.getItem('gaokao_paid_credits') || '0', 10);

            try {
                const payload = this.buildPayload();
                console.log('Sending request with progress:', payload);

                // Use SSE endpoint for progress updates
                const response = await fetch('/api/v1/analyze-with-progress', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream',
                        'X-Paid-Credits': String(paidCredits),
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    if (response.status === 429) {
                        const errorData = await response.json().catch(() => ({}));
                        this.error = errorData.detail || '今日请求次数已达上限，请明天再试。';
                        // Refresh usage display
                        const usageComp = document.querySelector('[x-data="usageData()"]');
                        if (usageComp && usageComp.__x) {
                            usageComp.__x.$data.fetchUsage();
                        }
                        throw new Error(this.error);
                    }
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Keep incomplete line in buffer

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                console.log('Progress update:', data);

                                // Check for error
                                if (data.error) {
                                    throw new Error(data.message);
                                }

                                // Update progress
                                this.progress = data.progress || 0;
                                this.progressMessage = data.message || '';
                                this.progressStep = data.step || 0;

                                // Check for final result
                                if (data.data) {
                                    this.report = data.data;
                                    console.log('Received report:', this.report);

                                    // Consume a paid credit
                                    const usageComp = document.querySelector('[x-data="usageData()"]');
                                    if (usageComp && usageComp.__x) {
                                        usageComp.__x.$data.consumeCredit();
                                        usageComp.__x.$data.fetchUsage();
                                    }
                                }
                            } catch (parseErr) {
                                console.warn('Failed to parse SSE data:', parseErr);
                            }
                        }
                    }
                }

                // Scroll to report if we got one
                if (this.report) {
                    this.$nextTick(() => {
                        const reportElement = document.getElementById('reportContent');
                        if (reportElement) {
                            reportElement.scrollIntoView({ behavior: 'smooth' });
                        }
                    });
                } else {
                    throw new Error('未收到分析报告，请重试');
                }

            } catch (err) {
                console.error('Analysis failed:', err);
                this.error = err.message || '分析过程中发生错误，请稍后重试';
            } finally {
                this.loading = false;
            }
        },

        // Render markdown to HTML
        renderMarkdown(markdown) {
            if (!markdown) return '';
            try {
                // Configure marked options
                marked.setOptions({
                    breaks: true,
                    gfm: true
                });
                return marked.parse(markdown);
            } catch (err) {
                console.error('Markdown rendering error:', err);
                return `<p class="text-red-500">报告渲染失败: ${err.message}</p>`;
            }
        },

        // Download report as HTML
        async downloadReport() {
            if (!this.report) return;

            try {
                const resp = await fetch('/api/v1/download-html', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        markdown_content: this.report.markdown_content,
                        student_name: this.student.name || '匿名'
                    })
                });

                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.detail || '下载失败');
                }

                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `高考志愿分析报告_${this.student.name || '匿名'}_${new Date().toISOString().slice(0, 10)}.html`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (err) {
                console.error('HTML download failed:', err);
                alert('下载失败：' + err.message);
            }
        }
    };
}

// Initialize marked.js when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set default marked options
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });
    }
});
