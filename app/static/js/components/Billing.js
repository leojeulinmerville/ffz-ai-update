console.log('🎯 Billing.js LOADED - Version 2024-12-04');

export default {
    data() {
        return {
            billingStatus: null,
            loading: true,
            processingCheckout: false,
            selectedPlan: 'monthly',
            promoCode: '',
            showPromoInput: false
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
        isBetaMode() {
            return !this.billingStatus?.enforcement_enabled;
        },
        hasAccess() {
            return this.billingStatus?.has_access || false;
        },
        currentPlanDisplay() {
            const status = this.billingStatus?.subscription?.status;
            if (status === 'active') {
                const plan = this.billingStatus?.subscription?.details?.plan || 'monthly';
                return plan === 'yearly' ? 'Season Pass (25 €/an)' : 'Mensuel (2,90 €/mois)';
            }
            if (this.isTrialActive) {
                return 'Essai gratuit';
            }
            return 'Aucun abonnement';
        },
        pricing() {
            return this.billingStatus?.pricing || {
                monthly: { price: 2.90, display: '2,90 €/mois' },
                yearly: { price: 25.00, display: '25 €/an (Season Pass)', savings: 'Économisez 28% !' }
            };
        }
    },
    methods: {
        async fetchBillingStatus() {
            this.loading = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/status', {
                    headers: { 'Authorization': 'Bearer ' + token }
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
        async createCheckout(plan) {
            this.processingCheckout = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/checkout', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + token,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plan: plan || this.selectedPlan,
                        promo_code: this.promoCode || null
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    window.location.href = data.checkout_url;
                } else {
                    const error = await res.json();
                    if (error.detail && error.detail.includes('Stripe')) {
                        alert('Stripe n\'est pas encore configuré. Fonctionnalité bientôt disponible !');
                    } else {
                        alert('Erreur: ' + (error.detail || 'Impossible de créer la session de paiement'));
                    }
                }
            } catch (e) {
                console.error('Checkout error:', e);
                alert('Le système de paiement n\'est pas encore actif. Profitez de l\'accès gratuit pendant la bêta !');
            } finally {
                this.processingCheckout = false;
            }
        },
        async openCustomerPortal() {
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/billing/portal', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token }
                });

                if (res.ok) {
                    const data = await res.json();
                    window.location.href = data.portal_url;
                } else {
                    alert('Le portail client n\'est pas encore disponible.');
                }
            } catch (e) {
                console.error('Failed to open portal:', e);
                alert('Le portail client sera bientôt disponible.');
            }
        }
    },
    template: `
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <!-- Header -->
            <div class="mb-8">
                <h2 class="text-3xl font-bold text-gray-900">Abonnement & Facturation</h2>
                <p class="mt-2 text-gray-600">Gérez votre abonnement FFZ Pass</p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p class="mt-4 text-gray-600">Chargement...</p>
            </div>

            <!-- Content -->
            <div v-else class="space-y-6">
                <!-- Beta Mode Banner -->
                <div v-if="isBetaMode" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <span class="text-2xl mr-3">🚀</span>
                        <div>
                            <h4 class="font-semibold text-blue-900">Mode Bêta</h4>
                            <p class="text-sm text-blue-700">
                                Le système de facturation sera bientôt activé. Profitez de toutes les fonctionnalités gratuitement pendant la bêta !
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Trial Banner (if trial active) -->
                <div v-if="isTrialActive && !isBetaMode" class="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-lg shadow-lg p-6 text-white">
                    <div class="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <h3 class="text-xl font-bold flex items-center">
                                🎉 Essai gratuit en cours
                            </h3>
                            <p class="mt-2 text-purple-100">
                                <span class="font-semibold text-2xl">{{ trialDaysRemaining }}</span> jours restants
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Current Plan Status -->
                <div class="bg-white rounded-lg shadow-md overflow-hidden">
                    <div class="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
                        <h3 class="text-xl font-bold text-white">Votre abonnement</h3>
                    </div>
                    
                    <div class="p-6">
                        <div class="flex items-center justify-between mb-6">
                            <div>
                                <p class="text-sm text-gray-500">Plan actuel</p>
                                <p class="text-xl font-bold text-gray-900">{{ currentPlanDisplay }}</p>
                            </div>
                            <div v-if="hasAccess" class="flex items-center">
                                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                                    ✓ Accès actif
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Plan Selection -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-lg font-bold text-gray-900 mb-4">Choisir un plan</h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <!-- Monthly Plan -->
                        <div 
                            @click="selectedPlan = 'monthly'" 
                            :class="[
                                'cursor-pointer rounded-lg border-2 p-4 transition-all',
                                selectedPlan === 'monthly' 
                                    ? 'border-indigo-500 bg-indigo-50' 
                                    : 'border-gray-200 hover:border-gray-300'
                            ]"
                        >
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="font-semibold text-gray-900">Mensuel</h4>
                                    <p class="text-2xl font-bold text-indigo-600">2,90 €<span class="text-sm text-gray-500">/mois</span></p>
                                </div>
                                <div v-if="selectedPlan === 'monthly'" class="text-indigo-600">
                                    <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            </div>
                            <p class="mt-2 text-sm text-gray-500">Flexibilité maximale, annulez à tout moment</p>
                        </div>

                        <!-- Yearly Plan -->
                        <div 
                            @click="selectedPlan = 'yearly'" 
                            :class="[
                                'cursor-pointer rounded-lg border-2 p-4 transition-all relative',
                                selectedPlan === 'yearly' 
                                    ? 'border-indigo-500 bg-indigo-50' 
                                    : 'border-gray-200 hover:border-gray-300'
                            ]"
                        >
                            <div class="absolute -top-2 -right-2">
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-500 text-white">
                                    -28%
                                </span>
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <h4 class="font-semibold text-gray-900">Season Pass</h4>
                                    <p class="text-2xl font-bold text-indigo-600">25 €<span class="text-sm text-gray-500">/an</span></p>
                                </div>
                                <div v-if="selectedPlan === 'yearly'" class="text-indigo-600">
                                    <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            </div>
                            <p class="mt-2 text-sm text-gray-500">Meilleur rapport qualité-prix pour les vrais fans</p>
                        </div>
                    </div>

                    <!-- Promo Code -->
                    <div class="mb-6">
                        <button 
                            v-if="!showPromoInput"
                            @click="showPromoInput = true" 
                            class="text-sm text-indigo-600 hover:text-indigo-800 flex items-center"
                        >
                            <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            Ajouter un code promo
                        </button>
                        <div v-else class="flex gap-2">
                            <input 
                                v-model="promoCode"
                                type="text" 
                                placeholder="Code promo (ex: FFZ_FAN_CLUB)"
                                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            >
                            <button 
                                @click="showPromoInput = false; promoCode = ''"
                                class="px-3 py-2 text-gray-500 hover:text-gray-700"
                            >
                                ✕
                            </button>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="flex gap-4">
                        <button 
                            @click="createCheckout(selectedPlan)"
                            :disabled="processingCheckout"
                            class="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 shadow-md"
                        >
                            <span v-if="processingCheckout">Chargement...</span>
                            <span v-else-if="selectedPlan === 'yearly'">💎 S'abonner au Season Pass (25 €/an)</span>
                            <span v-else>💎 S'abonner (2,90 €/mois)</span>
                        </button>
                    </div>

                    <!-- Subscription actions for existing subscribers -->
                    <div v-if="hasActiveSubscription" class="mt-4 pt-4 border-t border-gray-200">
                        <button 
                            @click="openCustomerPortal"
                            class="text-gray-600 hover:text-gray-800 text-sm"
                        >
                            ⚙️ Gérer mon abonnement / Annuler
                        </button>
                    </div>
                </div>

                <!-- Features Included -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-lg font-bold text-gray-900 mb-4">Inclus dans votre abonnement</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">⚽</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">1 équipe favorite</h4>
                                <p class="text-sm text-gray-600">Rapport IA personnalisé chaque semaine</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">📊</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Statistiques avancées</h4>
                                <p class="text-sm text-gray-600">xG, possession, tendances de forme</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">🌍</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Ligues majeures</h4>
                                <p class="text-sm text-gray-600">Premier League, La Liga, Serie A, Ligue 1...</p>
                            </div>
                        </div>
                        <div class="flex items-start space-x-3">
                            <span class="text-2xl">🎯</span>
                            <div>
                                <h4 class="font-semibold text-gray-900">Ton personnalisé</h4>
                                <p class="text-sm text-gray-600">Fan, Neutre ou Analytique</p>
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
                            <p class="text-sm text-gray-600 mt-1">Oui, vous pouvez annuler votre abonnement à tout moment. Aucun engagement.</p>
                        </div>
                        <div>
                            <h4 class="font-semibold text-gray-900">Que se passe-t-il après l'essai ?</h4>
                            <p class="text-sm text-gray-600 mt-1">Après 15 jours, choisissez entre le plan mensuel (2,90 €) ou le Season Pass (25 €/an).</p>
                        </div>
                        <div>
                            <h4 class="font-semibold text-gray-900">Quels moyens de paiement acceptez-vous ?</h4>
                            <p class="text-sm text-gray-600 mt-1">Toutes les cartes bancaires via Stripe (Visa, Mastercard, American Express).</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
