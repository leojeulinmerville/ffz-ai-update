export default {
    data() {
        return {
            form: {
                email: '',
                password: '',
                first_name: '',
                last_name: '',
                language: 'en',
                favorite_team: '',
                leagues: []
            },
            availableLeagues: [],
            loading: false,
            error: null,
            success: false
        }
    },
    async mounted() {
        // Fetch leagues for the dropdown
        try {
            const res = await fetch('/meta/leagues');
            if (res.ok) {
                this.availableLeagues = await res.json();
            }
        } catch (e) {
            console.error("Failed to load leagues", e);
        }
    },
    methods: {
        async register() {
            this.loading = true;
            this.error = null;
            try {
                // We need to create a public registration endpoint first, 
                // but for now we'll use the admin one or a new one we plan to build.
                // The plan says we will create app/api/public.py for this.
                // Let's assume the endpoint will be /api/public/register

                const res = await fetch('/api/public/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });

                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || 'Registration failed');
                }

                this.success = true;
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div class="max-w-md w-full space-y-8">
                <div>
                    <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Create your account</h2>
                </div>
                
                <div v-if="success" class="rounded-md bg-green-50 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <!-- Heroicon name: solid/check-circle -->
                            <svg class="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-green-800">Registration successful!</h3>
                            <div class="mt-2 text-sm text-green-700">
                                <p>Please check your email to verify your account.</p>
                            </div>
                            <div class="mt-4">
                                <router-link to="/login" class="text-sm font-medium text-green-600 hover:text-green-500">Go to Login &rarr;</router-link>
                            </div>
                        </div>
                    </div>
                </div>

                <form v-else class="mt-8 space-y-6" @submit.prevent="register">
                    <div class="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label class="sr-only">Email address</label>
                            <input v-model="form.email" type="email" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm" placeholder="Email address">
                        </div>
                        <div>
                            <label class="sr-only">Password</label>
                            <input v-model="form.password" type="password" required class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm" placeholder="Password">
                        </div>
                         <div>
                            <label class="sr-only">First Name</label>
                            <input v-model="form.first_name" type="text" class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm" placeholder="First Name">
                        </div>
                         <div>
                            <label class="sr-only">Last Name</label>
                            <input v-model="form.last_name" type="text" class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm" placeholder="Last Name">
                        </div>
                        <div>
                            <label class="sr-only">Favorite Team</label>
                            <input v-model="form.favorite_team" type="text" class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm" placeholder="Favorite Team (e.g. Bologna)">
                        </div>
                    </div>

                    <div v-if="error" class="text-red-500 text-sm text-center">{{ error }}</div>

                    <div>
                        <button type="submit" :disabled="loading" class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
                            <span v-if="loading">Creating account...</span>
                            <span v-else>Register</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `
}
