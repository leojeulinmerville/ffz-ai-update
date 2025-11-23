export default {
    template: `
        <div class="relative bg-white overflow-hidden">
            <div class="max-w-7xl mx-auto">
                <div class="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
                    <main class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                        <div class="sm:text-center lg:text-left">
                            <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                                <span class="block xl:inline">Your Weekly Football</span>
                                <span class="block text-indigo-600 xl:inline">AI Companion</span>
                            </h1>
                            <p class="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                                Get personalized, deep-dive weekly reports on your favorite team. We use AI Vision to analyze match reports, xG, and player ratings to give you the insights that matter.
                            </p>
                            <div class="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                                <div class="rounded-md shadow">
                                    <router-link to="/register" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10">
                                        Get Started
                                    </router-link>
                                </div>
                                <div class="mt-3 sm:mt-0 sm:ml-3">
                                    <router-link to="/login" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 md:py-4 md:text-lg md:px-10">
                                        Log In
                                    </router-link>
                                </div>
                            </div>
                        </div>
                    </main>
                </div>
            </div>
            <div class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 bg-gray-50 flex items-center justify-center">
                <div class="p-8">
                    <!-- Placeholder for a nice hero image or demo report -->
                    <div class="bg-white p-6 rounded-lg shadow-xl max-w-md mx-auto border border-gray-100">
                        <div class="flex items-center space-x-3 mb-4">
                            <div class="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-2xl">⚽</div>
                            <div>
                                <h3 class="font-bold text-gray-900">Bologna vs Roma</h3>
                                <p class="text-xs text-gray-500">AI Analysis • Just now</p>
                            </div>
                        </div>
                        <p class="text-sm text-gray-600 mb-3">
                            "Bologna is on fire! Orsolini's xG of 0.85 converted into a stunning brace. The high press forced 12 turnovers in the opposition half..."
                        </p>
                        <div class="h-2 bg-gray-100 rounded full overflow-hidden">
                            <div class="h-full bg-green-500 w-3/4"></div>
                        </div>
                        <div class="flex justify-between text-xs text-gray-400 mt-1">
                            <span>Dominance</span>
                            <span>75%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
