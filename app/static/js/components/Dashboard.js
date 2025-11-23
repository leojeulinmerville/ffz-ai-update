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
            availableLeagues: []
        }
    },
    async mounted() {
        await this.fetchProfile();
        await this.fetchLatestReport();
        await this.fetchLeagues();
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
        async fetchLatestReport() {
            this.loadingReport = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/news/latest', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    this.latestReport = await res.json();
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
                    this.availableLeagues = await res.json();
                }
            } catch (e) {
                console.error("Failed to load leagues", e);
            }
        },
        async generateReport() {
            this.loadingReport = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/news/generate', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    await this.fetchLatestReport();
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
            }
        }
    },
    template: `
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <!-- Header with Tabs -->
            <div class="mb-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">Tableau de bord</h2>
                <div class="border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8">
                        <button @click="activeTab = 'reports'" :class="activeTab === 'reports' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'" class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                            Rapports
                        </button>
                        <button @click="activeTab = 'settings'" :class="activeTab === 'settings' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'" class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                            Paramètres
                        </button>
                    </nav>
                </div>
            </div>

            <!-- Reports Tab -->
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
                            Généré le {{ new Date(latestReport.created_at).toLocaleDateString('fr-FR') }}
                        </p>
                    </div>
                    <div class="px-4 py-5 sm:p-6">
                        <div v-if="!latestReport && !loadingReport" class="text-center py-10 text-gray-500">
                            Aucun rapport généré. Cliquez sur le bouton ci-dessus pour commencer !
                        </div>
                        <div v-if="loadingReport && !latestReport" class="text-center py-10 text-gray-500">
                            Chargement...
                        </div>
                        
                        <div v-if="latestReport" class="space-y-8">
                            <div v-for="article in latestReport.report.articles" :key="article.league_code" class="border rounded-lg p-6 bg-gray-50">
                                <h4 class="text-xl font-bold text-indigo-900 mb-2">{{ article.headline }}</h4>
                                <div class="prose max-w-none text-gray-700 whitespace-pre-line mb-4">
                                    {{ article.narrative }}
                                </div>
                                
                                <div v-if="article.fan_spotlight" class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                                    <h3 class="text-sm font-medium text-yellow-800 mb-2">Focus club</h3>
                                    <div class="text-sm text-yellow-700 space-y-2">
                                        <p v-if="article.fan_spotlight.analysis"><strong>Analyse :</strong> {{ article.fan_spotlight.analysis }}</p>
                                        <p v-if="article.fan_spotlight.next_match_preview"><strong>Prochain match :</strong> {{ article.fan_spotlight.next_match_preview }}</p>
                                        <p v-if="article.fan_spotlight.tactical_notes"><strong>Tactique :</strong> {{ article.fan_spotlight.tactical_notes }}</p>
                                    </div>
                                </div>

                                <div v-if="article.watchlist && article.watchlist.length" class="bg-blue-50 rounded-md p-4">
                                    <h5 class="text-sm font-medium text-blue-800 mb-2">À surveiller</h5>
                                    <ul class="list-disc pl-5 text-sm text-blue-700">
                                        <li v-for="item in article.watchlist" :key="item">{{ item }}</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Settings Tab -->
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
                                <input v-model="settingsForm.favorite_team" type="text" class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="ex: Bologna">
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
                </div>

                <!-- Subscriptions -->
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

                        <!-- Add New Subscription -->
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
                        </div>
                    </div>
                </div>

                <!-- Danger Zone -->
                <div class="bg-white shadow sm:rounded-lg border-2 border-red-200">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg font-medium text-red-900 mb-2">Zone de danger</h3>
                        <p class="text-sm text-gray-500 mb-4">La suppression de votre compte est irréversible.</p>
                        <button @click="deleteAccount" class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700">
                            Supprimer mon compte
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
}
