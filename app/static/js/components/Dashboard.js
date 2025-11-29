console.log('🚀 Dashboard.js LOADED - Version 2024-11-24 15:57');

export default {
    data() {
        return {
            user: null,
            latestReport: null,
            loadingReport: false,
            activeTab: 'reports', // 'reports' or 'settings'
            settingsForm: {
                first_name: '',
                last_name: '',
                language: 'en',
                favorite_team: '',
                phone_number: ''
            },
            availableLanguages: [
                { code: 'en', name: 'English' },
                { code: 'fr', name: 'Français' },
                { code: 'es', name: 'Español' }
            ],
            subscriptions: [],
            newSubscription: {
                league: '',
                team: '',
                frequency: 'weekly'
            },
            availableLeagues: [],
            allTeams: [],
            billingStatus: null  // NEW: Track trial/subscription status
        }
    },
    async mounted() {
        await this.fetchProfile();
        await this.fetchBillingStatus();  // NEW: Fetch billing status
        await this.fetchLatestReport();
        await this.fetchLeagues();
        // Fetch teams for all leagues to populate the datalist (non-blocking)
        this.fetchAllTeams().catch(err => console.error('Failed to fetch teams:', err));
    },
    methods: {
        async fetchProfile() {
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/user/profile', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    this.user = data;
                    this.subscriptions = data.subscriptions || [];
                    // Populate settings form
                    this.settingsForm = {
                        first_name: data.first_name || '',
                        last_name: data.last_name || '',
                        language: data.language || 'en',
                        favorite_team: data.favorite_team || '',
                        phone_number: data.phone_number || ''
                    };
                }
            } catch (e) {
                console.error("Failed to fetch profile", e);
            }
        },
        async fetchBillingStatus() {
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    this.billingStatus = await res.json();
                }
            } catch (e) {
                console.error("Failed to fetch billing status", e);
            }
        },
        async fetchLatestReport() {
            this.loadingReport = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/reports/latest', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    this.latestReport = data.data; // New API returns {status, data}
                }
            } catch (e) {
                console.error("No latest report found");
            } finally {
                this.loadingReport = false;
            }
        },
        async fetchLeagues() {
            try {
                const res = await fetch('/meta/leagues');
                if (res.ok) {
                    const data = await res.json();
                    console.log('[DEBUG] Leagues API response:', data);
                    this.availableLeagues = data.leagues || [];
                    console.log('[DEBUG] availableLeagues set to:', this.availableLeagues);
                } else {
                    console.error('[DEBUG] Leagues fetch failed with status:', res.status);
                }
            } catch (e) {
                console.error("Failed to load leagues", e);
            }
        },
        async fetchAllTeams() {
            const teams = new Set();
            for (const league of this.availableLeagues) {
                try {
                    const res = await fetch(`/meta/leagues/${league.code}/teams`);
                    if (res.ok) {
                        const data = await res.json();
                        data.teams?.forEach(t => teams.add(t.name));
                    }
                } catch (e) {
                    console.error(`Failed to load teams for ${league.code}`, e);
                }
            }
            this.allTeams = Array.from(teams).sort();
        },
        async generateReport() {
            this.loadingReport = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/reports/generate', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    alert('✓ Rapport généré et envoyé par email !');
                    await this.fetchLatestReport();
                } else {
                    const error = await res.json();
                    alert(`Erreur: ${error.detail || 'Échec de la génération'}`);
                }
            } catch (e) {
                alert("Failed to generate report");
            } finally {
                this.loadingReport = false;
            }
        },
        async saveSettings() {
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.settingsForm)
                });
                if (res.ok) {
                    alert('✓ Paramètres mis à jour !');
                    await this.fetchProfile();
                }
            } catch (e) {
                alert("Erreur lors de la mise à jour");
            }
        },
        async addSubscription() {
            if (!this.newSubscription.league) return;

            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/user/subscriptions', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.newSubscription)
                });
                if (res.ok) {
                    this.newSubscription = { league: '', team: '', frequency: 'weekly' };
                    await this.fetchProfile();
                }
            } catch (e) {
                alert("Erreur lors de l'ajout");
            }
        },
        async deleteSubscription(subId) {
            if (!confirm('Supprimer cet abonnement ?')) return;

            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch(`/api/user/subscriptions/${subId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    await this.fetchProfile();
                }
            } catch (e) {
                alert("Erreur lors de la suppression");
            }
        },
        async deleteAccount() {
            if (!confirm('⚠️ ATTENTION : Supprimer définitivement votre compte ?')) return;
            if (!confirm('Cette action est irréversible. Êtes-vous sûr ?')) return;

            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/user/account', {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    localStorage.removeItem('ffz_token');
                    window.location.href = '/';
                }
            } catch (e) {
                alert("Erreur lors de la suppression");
                        </button >
                    <button @click="activeTab = 'settings'" : class="activeTab === 'settings' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'" class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" >
                        Paramètres
                        </button >
                    </nav >
                </div >
            </div >

            < !--Reports Tab-- >
            <div v-if="activeTab === 'reports'">
                <div class="flex justify-end mb-4">
                    <button @click="generateReport" :disabled="loadingReport" class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50">
                        <span v-if="loadingReport">Génération...</span>
                        <span v-else>Générer un nouveau rapport</span>
                    </button>
                </div>

                <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
                        <h3 class="text-lg font-medium text-gray-900">Dernier rapport</h3>
                        <p v-if="latestReport" class="mt-1 text-sm text-gray-500">
                            Généré le {{ latestReport.generated_at ? new Date(latestReport.generated_at).toLocaleDateString('fr-FR') : 'Date inconnue' }}
                        </p>
                    </div>
                    <div class="px-4 py-5 sm:p-6">
                        <div v-if="!latestReport && !loadingReport" class="text-center py-10 text-gray-500">
                            Aucun rapport généré. Cliquez sur le bouton ci-dessus pour commencer !
                        </div>
                        <div v-if="loadingReport && !latestReport" class="text-center py-10 text-gray-500">
                            Chargement...
                        </div>
                        
                        <div v-if="latestReport && latestReport.report" class="space-y-8">
                            <div v-if="latestReport.report.headline" class="text-center py-4 bg-indigo-50 rounded-lg">
                                <h2 class="text-2xl font-bold text-indigo-900">{{ latestReport.report.headline }}</h2>
                            </div>
                            
                            <div v-for="(section, idx) in latestReport.report.sections" :key="idx" class="border rounded-lg p-6 bg-gray-50">
                                <h4 class="text-xl font-bold text-indigo-900 mb-2">{{ section.title }}</h4>
                                <div class="prose max-w-none text-gray-700 whitespace-pre-line">
                                    {{ section.content }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div >
            </div >

            < !--Settings Tab-- >
                    <div v-if="activeTab === 'settings'" class="space-y-6">
                        <!-- Profile Settings -->
                        <div class="bg-white shadow sm:rounded-lg">
                            <div class="px-4 py-5 sm:p-6">
                                <h3 class="text-lg font-medium text-gray-900 mb-4">Profil</h3>
                                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Prénom</label>
                                        <input v-model="settingsForm.first_name" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Nom</label>
                                        <input v-model="settingsForm.last_name" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Langue des rapports</label>
                                        <select v-model="settingsForm.language" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                                            <option v-for="lang in availableLanguages" :key="lang.code" :value="lang.code">{{ lang.name }}</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Équipe préférée</label>
                                    <div class="mt-1 relative rounded-md shadow-sm">
                                        <input v-model="settingsForm.favorite_team" type="text" list="teams-list" class="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="Rechercher une équipe...">
                                            <datalist id="teams-list">
                                                <option v-for="team in allTeams" :key="team" :value="team" />
                                            </datalist>
                                    </div>
                                    <p class="mt-1 text-xs text-gray-500">Sélectionnez votre équipe de cœur pour des rapports personnalisés.</p>
                                </div>
                                <div class="sm:col-span-2">
                                    <label class="block text-sm font-medium text-gray-700">Téléphone (WhatsApp)</label>
                                    <input v-model="settingsForm.phone_number" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="+33...">
                                </div>
                            </div>
                            <div class="mt-4">
                                <button @click="saveSettings" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                                Enregistrer les modifications
                            </button>
                        </div>
                    </div>
                </div >

                < !--Subscriptions -->
                <div class="bg-white shadow sm:rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">Abonnements</h3>
                        
                        <!-- Current Subscriptions -->
                        <div v-if="subscriptions.length" class="mb-6">
                            <h4 class="text-sm font-medium text-gray-700 mb-2">Abonné à :</h4>
                            <div class="space-y-2">
                                <div v-for="sub in subscriptions" :key="sub.id" class="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                                    <div>
                                        <span class="font-medium">{{ sub.league }}</span>
                                        <span v-if="sub.team" class="text-gray-500"> - {{ sub.team }}</span>
                                    </div>
                                    <button @click="deleteSubscription(sub.id)" class="text-red-600 hover:text-red-800 text-sm">
                                        Supprimer
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!--Add New Subscription-- >
                    <div class="border-t pt-4">
                        <h4 class="text-sm font-medium text-gray-700 mb-2">Ajouter un abonnement :</h4>
                        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
                            <select v-model="newSubscription.league" class="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                                <option value="">Choisir une ligue...</option>
                                <option v-for="league in availableLeagues" :key="league.code" :value="league.code">
                                {{ league.name }}
                            </option>
                        </select>
                        <input v-model="newSubscription.team" type="text" placeholder="Équipe (optionnel)" class="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            <button @click="addSubscription" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                            Ajouter
                        </button>
                    </div>
                        </div >
                    </div >
                </div >

                < !--Danger Zone-- >
                    <div class="bg-white shadow sm:rounded-lg border-2 border-red-200">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg font-medium text-red-900 mb-2">Zone de danger</h3>
                            <p class="text-sm text-gray-500 mb-4">La suppression de votre compte est irréversible.</p>
                            <button @click="deleteAccount" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700">
                            Supprimer mon compte
                        </button>
                    </div>
                </div >
            </div >
        </div >
                    `
}
