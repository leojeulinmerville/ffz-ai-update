console.log('🎯 Billing.js LOADED - Version 2024-11-29');

export default {
    data() {
        return {
            user: null,
            billingStatus: null,
            loading: true,
            processingCheckout: false,
            stripePublishableKey: null
        }
    },
    async mounted() {
        await this.fetchBillingStatus();
    },
    computed: {
        trialDaysRemaining() {
            return this.billingStatus?.trial?.days_remaining || 0;
        },
        isTrialActive() {
            return this.billingStatus?.trial?.active || false;
        },
        hasActiveSubscription() {
            return this.billingStatus?.subscription?.status === 'active';
        },
        subscriptionStatus() {
            const status = this.billingStatus?.subscription?.status || 'trial';
            const statusMap = {
                'trial': { text: 'Essai gratuit', color: 'blue', icon: '🎉' },
                'active': { text: 'Actif', color: 'green', icon: '✅' },
                'cancelled': { text: 'Annulé', color: 'red', icon: '❌' },
                'past_due': { text: 'Paiement en retard', color: 'orange', icon: '⚠️' }
            };
            return statusMap[status] || statusMap['trial'];
        }
    },
    methods: {
        async fetchBillingStatus() {
            this.loading = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (res.ok) {
                    this.billingStatus = await res.json();
                }
            } catch (e) {
                console.error('Failed to fetch billing status:', e);
            } finally {
                this.loading = false;
            }
        },
        async createCheckout() {
            this.processingCheckout = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/checkout', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (res.ok) {
                    const data = await res.json();
                    // Redirect to Stripe Checkout
                    window.location.href = data.checkout_url;
                } else {
                    const error = await res.json();
                    alert(`Erreur: ${error.detail || 'Impossible de créer la session de paiement'}`);
                }
            } catch (e) {
                alert('Erreur lors de la création du checkout');
                console.error(e);
            } finally {
                this.processingCheckout = false;
            }
        },
        async openCustomerPortal() {
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/portal', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (res.ok) {
                    const data = await res.json();
                    window.location.href = data.portal_url;
                } else {
                    alert('Erreur lors de l\'ouverture du portail client');
                }
            } catch (e) {
                console.error('Failed to open portal:', e);
            }
        }
    },
    template: `
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <!-- Header -->
            <div class="mb-8">
                <h2 class="text-3xl font-bold text-gray-900">Abonnement & Facturation</h2>
                <p class="mt-2 text-gray-600">Gérez votre abonnement FFZ Premium</p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p class="mt-4 text-gray-600">Chargement...</p>
            </div>

            <!-- Content -->
            <div v-else class="space-y-6">
                <!-- Trial Banner (if trial active) -->
                <div v-if="isTrialActive" class="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg shadow-lg p-6 text-white">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-xl font-bold flex items-center">
                                🎉 Essai gratuit en cours
                            </h3>
                            <p class="mt-2 text-purple-100">
                                <span class="font-semibold text-2xl">{{ trialDaysRemaining }}</span> jours restants
                            </p>
                            <p class="mt-1 text-sm text-purple-100">
                                Profitez de toutes les fonctionnalités premium gratuitement
                            </p>
                        </div>
                        <button 
                            @click="createCheckout"
                            :disabled="processingCheckout"
                            class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50 shadow-md"
                        >
                            <span v-if="processingCheckout">Chargement...</span>
                            <span v-else>S'abonner maintenant →</span>
                        </button>
                    </div>
                </div>

                <!-- Subscription Card -->
                <div class="bg-white rounded-lg shadow-md overflow-hidden">
                    <div class="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
                        <h3 class="text-xl font-bold text-white flex items-center">
                            {{ subscriptionStatus.icon }} Statut de l'abonnement
                        </h3>
                    </div>
                    
                    <div class="p-6">
                        <!-- Status Badge -->
                        <div class="flex items-center justify-between mb-6">
                            <div>
                                <span :class="{
                                    'bg-blue-100 text-blue-800': subscriptionStatus.color === 'blue',
                                    'bg-green-100 text-green-800': subscriptionStatus.color === 'green',
                                    'bg-red-100 text-red-800': subscriptionStatus.color === 'red',
                                    'bg-orange-100 text-orange-800': subscriptionStatus.color === 'orange'
                                }" class="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold">
                                    {{ subscriptionStatus.text }}
                                </span>
                            </div>
                            <div v-if="hasActiveSubscription" class="text-right">
                                <p class="text-2xl font-bold text-gray-900">€1<span class="text-sm text-gray-500">/mois</span></p>
                                <p class="text-xs text-gray-500">Facturation mensuelle</p>
                            </div>
                        </div>

                        <!-- Trial Info -->
                        <div v-if="isTrialActive" class="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
                            <h4 class="font-semibold text-purple-900 mb-2">Période d'essai</h4>
                            <div class="space-y-2 text-sm text-purple-800">
                                <p>✓ Accès complet à toutes les fonctionnalités</p>
                                <p>✓ Rapports hebdomadaires personnalisés</p>
                                <p>✓ Support multi-langues (FR/EN/ES)</p>
                                <p>✓ 4 styles de ton (Fan/Neutre/Analytique/Parieur)</p>
                            </div>
                        </div>

                        <!-- Active Subscription Info -->
                        <div v-if="hasActiveSubscription" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                            <h4 class="font-semibold text-green-900 mb-2">Abonnement Premium Actif</h4>
                            <div class="space-y-2 text-sm text-green-800">
                                <p>✓ Équipes et ligues illimitées</p>
                                <p>✓ Rapports personnalisés hebdomadaires</p>
                                <p>✓ Livraison par email automatique</p>
                                <p>✓ Support prioritaire</p>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="flex gap-4">
                            <button 
                                v-if="!hasActiveSubscription"
                                @click="createCheckout"
                                :disabled="processingCheckout"
                                class="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 shadow-md"
                            >
                                <span v-if="processingCheckout">Chargement...</span>
                                <span v-else>💎 S'abonner pour €1/mois</span>
                            </button>
                            
                            <button 
                                v-if="hasActiveSubscription"
                                @click="openCustomerPortal"
                                class="flex-1 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                            >
                                ⚙️ Gérer l'abonnement
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Features Card -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-lg font-bold text-gray-900 mb-4">Fonctionnalités Premium</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">⚽</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Équipes illimitées</h4>
                                <p class="text-sm text-gray-600">Suivez autant d'équipes que vous voulez</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">📊</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Analyses détaillées</h4>
                                <p class="text-sm text-gray-600">Stats xG, possession, tendances</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">🌍</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Multi-langues</h4>
                                <p class="text-sm text-gray-600">Français, Anglais, Espagnol</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">📧</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Email automatique</h4>
                                <p class="text-sm text-gray-600">Recevez vos rapports chaque semaine</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- FAQ -->
                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-lg font-bold text-gray-900 mb-4">Questions fréquentes</h3>
                    <div class="space-y-4">
                        <div>
                            <h4 class="font-semibold text-gray-900">Puis-je annuler à tout moment ?</h4>
                            <p class="text-sm text-gray-600 mt-1">Oui, vous pouvez annuler votre abonnement à tout moment depuis le portail client. Aucun engagement.</p>
                        </div>
                        <div>
                            <h4 class="font-semibold text-gray-900">Que se passe-t-il après l'essai ?</h4>
                            <p class="text-sm text-gray-600 mt-1">Après 15 jours, vous devrez souscrire à €1/mois pour continuer à accéder aux fonctionnalités premium.</p>
                        </div>
                        <div>
                            <h4 class="font-semibold text-gray-900">Quels moyens de paiement acceptez-vous ?</h4>
                            <p class="text-sm text-gray-600 mt-1">Nous acceptons toutes les cartes bancaires via Stripe (Visa, Mastercard, American Express).</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
