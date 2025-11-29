const { ref, reactive, computed } = Vue;

export default {
    template: `
        <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div class="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    Welcome to FFZ!
                </h2>
                <p class="mt-2 text-center text-sm text-gray-600">
                    Let's personalize your experience.
                </p>
            </div>

            <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <!-- Progress Bar -->
                    <div class="mb-8">
                        <div class="relative pt-1">
                            <div class="flex mb-2 items-center justify-between">
                                <div>
                                    <span class="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-indigo-600 bg-indigo-200">
                                        Step {{ step }} of 3
                                    </span>
                                </div>
                            </div>
                            <div class="overflow-hidden h-2 mb-4 text-xs flex rounded bg-indigo-200">
                                <div :style="{ width: (step / 3) * 100 + '%' }" class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-500 transition-all duration-500"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Step 1: Language -->
                    <div v-if="step === 1">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Choose your language</h3>
                        <div class="space-y-4">
                            <div v-for="lang in languages" :key="lang.code" 
                                @click="form.language = lang.code"
                                :class="{'ring-2 ring-indigo-500 border-transparent': form.language === lang.code, 'border-gray-300': form.language !== lang.code}"
                                class="relative block border rounded-lg p-4 cursor-pointer hover:border-indigo-500 focus:outline-none">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ lang.name }}
                                        </div>
                                    </div>
                                    <div v-if="form.language === lang.code" class="text-indigo-600">
                                        <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Team -->
                    <div v-if="step === 2">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Who do you support?</h3>
                        <div>
                            <label for="team" class="block text-sm font-medium text-gray-700">Search Team</label>
                            <div class="mt-1">
                                <input type="text" v-model="searchQuery" @input="filterTeams" placeholder="e.g. Arsenal, PSG, Real Madrid" class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            </div>
                            <div v-if="filteredTeams.length > 0" class="mt-2 max-h-60 overflow-y-auto border border-gray-200 rounded-md">
                                <div v-for="team in filteredTeams" :key="team" 
                                    @click="selectTeam(team)"
                                    class="p-3 hover:bg-gray-50 cursor-pointer text-sm text-gray-700 border-b last:border-b-0">
                                    {{ team }}
                                </div>
                            </div>
                            <div v-if="form.favorite_team" class="mt-4 p-4 bg-indigo-50 rounded-md flex justify-between items-center">
                                <span class="font-medium text-indigo-700">{{ form.favorite_team }}</span>
                                <button @click="form.favorite_team = ''" class="text-indigo-500 hover:text-indigo-700 text-sm">Change</button>
                            </div>
                        </div>
                    </div>

                    <!-- Step 3: Tone -->
                    <div v-if="step === 3">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">How do you want your news?</h3>
                        <div class="space-y-4">
                            <div v-for="tone in tones" :key="tone.value" 
                                @click="form.tone = tone.value"
                                :class="{'ring-2 ring-indigo-500 border-transparent': form.tone === tone.value, 'border-gray-300': form.tone !== tone.value}"
                                class="relative block border rounded-lg p-4 cursor-pointer hover:border-indigo-500 focus:outline-none">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ tone.label }}
                                        </div>
                                        <div class="text-sm text-gray-500">
                                            {{ tone.description }}
                                        </div>
                                    </div>
                                    <div v-if="form.tone === tone.value" class="text-indigo-600">
                                        <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Navigation Buttons -->
                    <div class="mt-8 flex justify-between">
                        <button v-if="step > 1" @click="step--" class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Back
                        </button>
                        <div v-else></div> <!-- Spacer -->

                        <button v-if="step < 3" @click="nextStep" :disabled="!canProceed" :class="{'opacity-50 cursor-not-allowed': !canProceed}" class="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Next
                        </button>
                        <button v-else @click="submit" :disabled="isSubmitting" class="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            {{ isSubmitting ? 'Saving...' : 'Finish' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const router = VueRouter.useRouter();
        const step = ref(1);
        const isSubmitting = ref(false);
        const searchQuery = ref('');
        const filteredTeams = ref([]);

        const form = reactive({
            language: 'en',
            favorite_team: '',
            tone: 'neutral'
        });

        const languages = [
            { code: 'en', name: 'English' },
            { code: 'fr', name: 'Français' },
            { code: 'es', name: 'Español' },
            { code: 'de', name: 'Deutsch' },
            { code: 'it', name: 'Italiano' }
        ];

        const tones = [
            { value: 'fan', label: 'Fan', description: 'Passionate, biased, and emotional.' },
            { value: 'neutral', label: 'Neutral', description: 'Objective, balanced, and factual.' },
            { value: 'analytic', label: 'Analytic', description: 'Data-driven, tactical, and deep.' }
        ];

        // Mock teams for now - replace with API call later
        const allTeams = [
            'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Liverpool', 'Luton Town', 'Man City', 'Man Utd', 'Newcastle', 'Nottm Forest', 'Sheffield Utd', 'Tottenham', 'West Ham', 'Wolves',
            'PSG', 'Marseille', 'Lyon', 'Monaco', 'Lille', 'Lens', 'Rennes', 'Nice',
            'Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla', 'Valencia',
            'Bayern Munich', 'Dortmund', 'Leverkusen', 'Leipzig',
            'Inter', 'Milan', 'Juventus', 'Napoli', 'Roma'
        ];

        const filterTeams = () => {
            if (searchQuery.value.length < 2) {
                filteredTeams.value = [];
                return;
            }
            const query = searchQuery.value.toLowerCase();
            filteredTeams.value = allTeams.filter(team => team.toLowerCase().includes(query));
        };

        const selectTeam = (team) => {
            form.favorite_team = team;
            searchQuery.value = '';
            filteredTeams.value = [];
        };

        const canProceed = computed(() => {
            if (step.value === 1) return !!form.language;
            if (step.value === 2) return !!form.favorite_team;
            if (step.value === 3) return !!form.tone;
            return false;
        });

        const nextStep = () => {
            if (canProceed.value) {
                step.value++;
            }
        };

        const submit = async () => {
            isSubmitting.value = true;
            try {
                const token = localStorage.getItem('ffz_token');
                const res = await fetch('/api/onboarding/preferences', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(form)
                });

                if (res.ok) {
                    router.push('/dashboard');
                } else {
                    alert('Something went wrong. Please try again.');
                }
            } catch (e) {
                console.error(e);
                alert('Network error. Please try again.');
            } finally {
                isSubmitting.value = false;
            }
        };

        return {
            step,
            form,
            languages,
            tones,
            searchQuery,
            filteredTeams,
            filterTeams,
            selectTeam,
            canProceed,
            nextStep,
            submit,
            isSubmitting
        };
    }
}
