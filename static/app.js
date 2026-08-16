document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        currentTab: 'generator', // generator, llm, gitlab
        llms: [],
        gitlabs: [],
        projects: [],
        
        newLLM: { provider: 'gemini', model_name: '', api_key: '', base_url: '' },
        newGitLab: { name: '', gitlab_url: '', token: '' },
        
        report: { instance_id: '', project_id: '', target_doc_id: '', start_date: '', end_date: '' },
        
        // Stepper & Commit Validation State
        currentStep: 1,
        isCheckingCommits: false,
        commitsChecked: false,
        totalCommitsFound: 0,
        previewCommits: [],
        commitCheckStatus: { type: '', message: '' },

        projectsLoading: false,
        isGenerating: false,
        status: { type: '', message: '' },
        
        llmTestStatus: { type: '', message: '' },
        isTestingLLM: false,
        editingLLMId: null,

        async init() {
            // Coba restore tab terakhir jika ada (opsional)
            this.fetchLLMs();
            this.fetchGitLabs();
        },

        async fetchLLMs() {
            const res = await fetch('/api/config/llm');
            this.llms = await res.json();
        },
        
        async addLLM() {
            if (this.editingLLMId) {
                await fetch(`/api/config/llm/${this.editingLLMId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...this.newLLM})
                });
                this.editingLLMId = null;
            } else {
                await fetch('/api/config/llm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...this.newLLM, is_active: this.llms.length === 0})
                });
            }
            this.newLLM = { provider: 'gemini', model_name: '', api_key: '', base_url: '' };
            this.fetchLLMs();
        },
        
        editLLM(llm) {
            this.editingLLMId = llm.id;
            this.newLLM = { 
                provider: llm.provider, 
                model_name: llm.model_name, 
                api_key: llm.api_key || '', 
                base_url: llm.base_url || '' 
            };
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        },
        
        cancelEditLLM() {
            this.editingLLMId = null;
            this.newLLM = { provider: 'gemini', model_name: '', api_key: '', base_url: '' };
        },

        async testExistingLLM(llm) {
            this.llmTestStatus = { type: 'info', message: `Testing connection to ${llm.provider}...` };
            try {
                const res = await fetch('/api/config/llm/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...llm, is_active: false})
                });
                const result = await res.json();
                if (res.ok) {
                    this.llmTestStatus = { type: 'success', message: `✅ Connection to ${llm.model_name} successful!` };
                } else {
                    this.llmTestStatus = { type: 'error', message: `❌ Failed: ${result.detail || 'Unknown error'}` };
                }
            } catch (e) {
                this.llmTestStatus = { type: 'error', message: `❌ Network Error: ${e.message}` };
            }
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        },
        
        async testLLM() {
            if (!this.newLLM.model_name) {
                this.llmTestStatus = { type: 'error', message: 'Model Name is required' };
                return;
            }
            this.isTestingLLM = true;
            this.llmTestStatus = { type: 'info', message: 'Testing connection to ' + this.newLLM.provider + '...' };
            try {
                const res = await fetch('/api/config/llm/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...this.newLLM, is_active: false})
                });
                const result = await res.json();
                if (res.ok) {
                    this.llmTestStatus = { type: 'success', message: '✅ Connection successful!' };
                } else {
                    this.llmTestStatus = { type: 'error', message: `❌ Failed: ${result.detail || 'Unknown error'}` };
                }
            } catch (e) {
                this.llmTestStatus = { type: 'error', message: `❌ Network Error: ${e.message}` };
            } finally {
                this.isTestingLLM = false;
            }
        },
        
        async activateLLM(id) {
            await fetch(`/api/config/llm/${id}/activate`, { method: 'PUT' });
            this.fetchLLMs();
        },

        async deleteLLM(id) {
            if(!confirm('Delete this LLM configuration?')) return;
            await fetch(`/api/config/llm/${id}`, { method: 'DELETE' });
            this.fetchLLMs();
        },

        async fetchGitLabs() {
            const res = await fetch('/api/config/gitlab');
            this.gitlabs = await res.json();
        },

        async addGitLab() {
            await fetch('/api/config/gitlab', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.newGitLab)
            });
            this.newGitLab = { name: '', gitlab_url: '', token: '' };
            this.fetchGitLabs();
        },

        async deleteGitLab(id) {
            if(!confirm('Delete this GitLab Instance?')) return;
            await fetch(`/api/config/gitlab/${id}`, { method: 'DELETE' });
            this.fetchGitLabs();
            if(this.report.instance_id == id) {
                this.report.instance_id = '';
                this.projects = [];
                this.resetCommitCheck();
            }
        },

        async fetchProjects() {
            this.resetCommitCheck();
            if (!this.report.instance_id) {
                this.projects = [];
                return;
            }
            this.projectsLoading = true;
            try {
                const res = await fetch(`/api/config/gitlab/${this.report.instance_id}/projects`);
                if (!res.ok) throw new Error(await res.text());
                this.projects = await res.json();
            } catch (e) {
                alert("Failed to fetch projects: " + e.message);
                this.projects = [];
            } finally {
                this.projectsLoading = false;
            }
        },

        resetCommitCheck() {
            this.commitsChecked = false;
            this.totalCommitsFound = 0;
            this.previewCommits = [];
            this.commitCheckStatus = { type: '', message: '' };
        },

        async checkCommits() {
            if (!this.report.instance_id || !this.report.project_id || !this.report.start_date || !this.report.end_date) {
                this.commitCheckStatus = { 
                    type: 'error', 
                    message: '❌ Harap lengkapi GitLab instance, proyek, dan rentang tanggal.' 
                };
                return;
            }

            if (this.report.start_date > this.report.end_date) {
                this.commitCheckStatus = { 
                    type: 'error', 
                    message: '❌ Tanggal mulai (Start Date) harus sebelum atau sama dengan tanggal akhir (End Date).' 
                };
                return;
            }

            this.commitsChecked = false;
            this.totalCommitsFound = 0;
            this.previewCommits = [];
            this.isCheckingCommits = true;
            this.commitCheckStatus = { type: 'info', message: 'Mengecek commit di GitLab...' };

            try {
                const params = new URLSearchParams({
                    instance_id: this.report.instance_id,
                    project_id: this.report.project_id,
                    start_date: this.report.start_date,
                    end_date: this.report.end_date
                });
                const res = await fetch(`/api/test-gitlab?${params.toString()}`);
                const result = await res.json();

                if (res.ok) {
                    this.totalCommitsFound = result.total_commits || 0;
                    this.previewCommits = result.sample_commits || [];
                    this.commitsChecked = true;

                    if (this.totalCommitsFound > 0) {
                        this.commitCheckStatus = { 
                            type: 'success', 
                            message: `✅ Ditemukan ${this.totalCommitsFound} commit siap dianalisis.` 
                        };
                    } else {
                        this.commitCheckStatus = { 
                            type: 'warning', 
                            message: '⚠️ Tidak ada commit ditemukan pada rentang tanggal tersebut. Silakan ubah tanggal.' 
                        };
                    }
                } else {
                    this.commitCheckStatus = { 
                        type: 'error', 
                        message: `❌ Gagal mengambil data commit: ${result.detail || 'Terjadi kesalahan pada server.'}` 
                    };
                }
            } catch (error) {
                this.commitCheckStatus = { 
                    type: 'error', 
                    message: `❌ Gagal mengambil data commit: ${error.message}` 
                };
            } finally {
                this.isCheckingCommits = false;
            }
        },

        nextStep() {
            if (this.currentStep === 1) {
                if (!this.report.instance_id || !this.report.project_id) {
                    this.status = { type: 'error', message: '❌ Silakan pilih GitLab Instance dan Project terlebih dahulu.' };
                    return;
                }
                this.status = { type: '', message: '' };
                this.currentStep = 2;
            } else if (this.currentStep === 2) {
                if (!this.commitsChecked) {
                    this.commitCheckStatus = { type: 'error', message: '❌ Silakan klik "Cek & Preview Commit" terlebih dahulu.' };
                    return;
                }
                if (this.totalCommitsFound <= 0) {
                    this.commitCheckStatus = { type: 'warning', message: '⚠️ Tidak ada commit untuk dianalisis. Ubah rentang tanggal dan cek kembali.' };
                    return;
                }
                this.status = { type: '', message: '' };
                this.currentStep = 3;
            }
        },

        prevStep() {
            if (this.currentStep > 1) {
                this.currentStep--;
            }
        },

        goToStep(step) {
            if (step === 1) {
                this.currentStep = 1;
            } else if (step === 2) {
                if (!this.report.instance_id || !this.report.project_id) {
                    this.status = { type: 'error', message: '❌ Silakan pilih GitLab Instance dan Project terlebih dahulu.' };
                    return;
                }
                this.currentStep = 2;
            } else if (step === 3) {
                if (!this.report.instance_id || !this.report.project_id) {
                    this.status = { type: 'error', message: '❌ Silakan pilih GitLab Instance dan Project di Langkah 1.' };
                    return;
                }
                if (!this.commitsChecked || this.totalCommitsFound <= 0) {
                    this.commitCheckStatus = { type: 'warning', message: '⚠️ Lakukan pengecekan commit di Langkah 2 terlebih dahulu.' };
                    this.currentStep = 2;
                    return;
                }
                this.currentStep = 3;
            }
        },

        async generateReport() {
            // Issue #1: Client-side validation
            if (!this.report.instance_id || !this.report.project_id || !this.report.start_date || !this.report.end_date || !this.report.target_doc_id) {
                this.status = { type: 'error', message: '<strong>❌ Validation Error:</strong> Please fill in all fields.' };
                return;
            }

            // Issue #7: Date range validation
            if (this.report.start_date > this.report.end_date) {
                this.status = { type: 'error', message: '<strong>❌ Validation Error:</strong> Start date must be before end date.' };
                return;
            }

            this.isGenerating = true;
            this.status = { type: 'info', message: 'Fetching commits and analyzing with AI... This may take up to 60 seconds.' };
            
            // Issue #2: AbortController with timeout
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 120_000);

            try {
                // Issue #3 & #4: Send data as JSON body instead of query params
                const response = await fetch('/api/generate-report/full-pipeline', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        instance_id: parseInt(this.report.instance_id),
                        project_id: this.report.project_id,
                        start_date: this.report.start_date,
                        end_date: this.report.end_date,
                        target_doc_id: this.report.target_doc_id
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeout);
                const result = await response.json();

                if (response.ok) {
                    // Issue #5: Defensive access on response fields
                    const clusters = result.total_clusters ?? 'N/A';
                    this.status = { type: 'success', message: `<strong>✅ Success!</strong><br>${result.message || 'Report generated.'}<br>Total Clusters: ${clusters}` };
                } else {
                    this.status = { type: 'error', message: `<strong>❌ Failed:</strong> ${result.detail || "Internal Server Error"}` };
                }
            } catch (error) {
                clearTimeout(timeout);
                // Issue #6: AbortError-aware error message
                const msg = error.name === 'AbortError' ? 'Request timed out. The AI pipeline may still be running on the server.' : error.message;
                this.status = { type: 'error', message: `<strong>❌ Network Error:</strong> ${msg}` };
            } finally {
                this.isGenerating = false;
            }
        }
    }));
});
