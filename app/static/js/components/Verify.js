export default {
    data() {
        return {
            status: 'verifying', // verifying, success, error
            message: 'Verifying your email...'
        }
    },
    async mounted() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            this.status = 'error';
            this.message = 'Missing verification token.';
            return;
        }

        try {
            const res = await fetch(`/api/public/verify?token=${token}`, {
                method: 'POST'
            });

            if (res.ok) {
                this.status = 'success';
                this.message = 'Email verified successfully! You can now login.';
            } else {
                const data = await res.json();
                throw new Error(data.detail || 'Verification failed');
            }
        } catch (e) {
            this.status = 'error';
            this.message = e.message;
        }
    },
    template: `
                < div class= "min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8" >
                <div class="max-w-md w-full space-y-8 text-center">
                    <div v-if="status === 'verifying'" class="text-gray-600">
                        <svg class="animate-spin h-10 w-10 mx-auto mb-4 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {{ message }}
                    </div>

                    <div v-if="status === 'success'" class="text-green-600">
                        <svg class="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h2 class="text-2xl font-bold mb-2">Verified!</h2>
                        <p class="mb-6">{{ message }}</p>
                        <router-link to="/login" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                            Go to Login
                        </router-link>
                    </div>

                    <div v-if="status === 'error'" class="text-red-600">
                        <svg class="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h2 class="text-2xl font-bold mb-2">Verification Failed</h2>
                        <p>{{ message }}</p>
                    </div>
                </div>
        </div >
                `
}
