export default {
    template: `
        <div class="bg-white">
            <!-- Hero Section -->
            <div class="relative overflow-hidden bg-white">
                <div class="mx-auto max-w-7xl">
                    <div class="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
                        <main class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                            <div class="sm:text-center lg:text-left">
                                <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                                    <span class="block xl:inline">Your Football World,</span>
                                    <span class="block text-indigo-600 xl:inline">Curated by AI.</span>
                                </h1>
                                <p class="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                                    Get personalized weekly reports on your favorite teams and leagues. Deep stats, key insights, and a tone that matches your passion.
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
                <div class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
                    <img class="h-56 w-full object-cover sm:h-72 md:h-96 lg:w-full lg:h-full" src="https://images.unsplash.com/photo-1508098682722-e99c43a406b2?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80" alt="Football stadium">
                </div>
            </div>

            <!-- Features Section -->
            <div class="py-12 bg-gray-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="lg:text-center">
                        <h2 class="text-base text-indigo-600 font-semibold tracking-wide uppercase">Features</h2>
                        <p class="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
                            Everything you need to stay ahead
                        </p>
                        <p class="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
                            Stop scrolling through endless feeds. We distill the noise into actionable insights.
                        </p>
                    </div>

                    <div class="mt-10">
                        <dl class="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
                            <div class="relative">
                                <dt>
                                    <div class="absolute flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white">
                                        <!-- Heroicon name: outline/globe-alt -->
                                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                        </svg>
                                    </div>
                                    <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Global Coverage</p>
                                </dt>
                                <dd class="mt-2 ml-16 text-base text-gray-500">
                                    From the Premier League to Ligue 1, we cover the major leagues that matter to you.
                                </dd>
                            </div>

                            <div class="relative">
                                <dt>
                                    <div class="absolute flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white">
                                        <!-- Heroicon name: outline/lightning-bolt -->
                                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                    </div>
                                    <p class="ml-16 text-lg leading-6 font-medium text-gray-900">AI-Powered Insights</p>
                                </dt>
                                <dd class="mt-2 ml-16 text-base text-gray-500">
                                    Our AI analyzes thousands of data points to bring you stats and stories you won't find elsewhere.
                                </dd>
                            </div>

                            <div class="relative">
                                <dt>
                                    <div class="absolute flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white">
                                        <!-- Heroicon name: outline/annotation -->
                                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                                        </svg>
                                    </div>
                                    <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Personalized Tone</p>
                                </dt>
                                <dd class="mt-2 ml-16 text-base text-gray-500">
                                    Choose how you want your news: passionate Fan, objective Neutral, or data-driven Analytic.
                                </dd>
                            </div>

                            <div class="relative">
                                <dt>
                                    <div class="absolute flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white">
                                        <!-- Heroicon name: outline/scale -->
                                        <svg class="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                                        </svg>
                                    </div>
                                    <p class="ml-16 text-lg leading-6 font-medium text-gray-900">Weekly Digest</p>
                                </dt>
                                <dd class="mt-2 ml-16 text-base text-gray-500">
                                    Get a comprehensive report delivered to your inbox or dashboard every week.
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>

            <!-- Pricing Section -->
            <div class="bg-gray-900">
                <div class="pt-12 sm:pt-16 lg:pt-24">
                    <div class="max-w-7xl mx-auto text-center px-4 sm:px-6 lg:px-8">
                        <div class="max-w-3xl mx-auto space-y-2 lg:max-w-none">
                            <h2 class="text-lg leading-6 font-semibold text-gray-300 uppercase tracking-wider">Pricing</h2>
                            <p class="text-3xl font-extrabold text-white sm:text-4xl lg:text-5xl">
                                The right price for you, whoever you are
                            </p>
                            <p class="text-xl text-gray-300">
                                Start with a free trial. No credit card required.
                            </p>
                        </div>
                    </div>
                </div>
                <div class="mt-8 pb-12 bg-gray-50 sm:mt-12 sm:pb-16 lg:pb-24">
                    <div class="relative">
                        <div class="absolute inset-0 h-3/4 bg-gray-900"></div>
                        <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                            <div class="max-w-md mx-auto space-y-4 lg:max-w-5xl lg:grid lg:grid-cols-2 lg:gap-5 lg:space-y-0">
                                <div class="flex flex-col rounded-lg shadow-lg overflow-hidden">
                                    <div class="px-6 py-8 bg-white sm:p-10 sm:pb-6">
                                        <div>
                                            <h3 class="inline-flex px-4 py-1 rounded-full text-sm font-semibold tracking-wide uppercase bg-indigo-100 text-indigo-600" id="tier-standard">
                                                Standard
                                            </h3>
                                        </div>
                                        <div class="mt-4 flex items-baseline text-6xl font-extrabold">
                                            $0
                                            <span class="ml-1 text-2xl font-medium text-gray-500">/mo</span>
                                        </div>
                                        <p class="mt-5 text-lg text-gray-500">
                                            Perfect for casual fans.
                                        </p>
                                    </div>
                                    <div class="flex-1 flex flex-col justify-between px-6 pt-6 pb-8 bg-gray-50 space-y-6 sm:p-10 sm:pt-6">
                                        <ul class="space-y-4">
                                            <li class="flex items-start">
                                                <div class="flex-shrink-0">
                                                    <svg class="h-6 w-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <p class="ml-3 text-base text-gray-700">1 Team</p>
                                            </li>
                                            <li class="flex items-start">
                                                <div class="flex-shrink-0">
                                                    <svg class="h-6 w-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <p class="ml-3 text-base text-gray-700">Weekly Summary</p>
                                            </li>
                                        </ul>
                                        <div class="rounded-md shadow">
                                            <router-link to="/register" class="flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-gray-800 hover:bg-gray-900" aria-describedby="tier-standard">
                                                Get started
                                            </router-link>
                                        </div>
                                    </div>
                                </div>

                                <div class="flex flex-col rounded-lg shadow-lg overflow-hidden">
                                    <div class="px-6 py-8 bg-white sm:p-10 sm:pb-6">
                                        <div>
                                            <h3 class="inline-flex px-4 py-1 rounded-full text-sm font-semibold tracking-wide uppercase bg-indigo-100 text-indigo-600" id="tier-premium">
                                                Premium
                                            </h3>
                                        </div>
                                        <div class="mt-4 flex items-baseline text-6xl font-extrabold">
                                            $9
                                            <span class="ml-1 text-2xl font-medium text-gray-500">/mo</span>
                                        </div>
                                        <p class="mt-5 text-lg text-gray-500">
                                            For the die-hard supporters.
                                        </p>
                                    </div>
                                    <div class="flex-1 flex flex-col justify-between px-6 pt-6 pb-8 bg-gray-50 space-y-6 sm:p-10 sm:pt-6">
                                        <ul class="space-y-4">
                                            <li class="flex items-start">
                                                <div class="flex-shrink-0">
                                                    <svg class="h-6 w-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <p class="ml-3 text-base text-gray-700">Unlimited Teams</p>
                                            </li>
                                            <li class="flex items-start">
                                                <div class="flex-shrink-0">
                                                    <svg class="h-6 w-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <p class="ml-3 text-base text-gray-700">Deep Analytics</p>
                                            </li>
                                            <li class="flex items-start">
                                                <div class="flex-shrink-0">
                                                    <svg class="h-6 w-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <p class="ml-3 text-base text-gray-700">Custom Tone</p>
                                            </li>
                                        </ul>
                                        <div class="rounded-md shadow">
                                            <router-link to="/register" class="flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700" aria-describedby="tier-premium">
                                                Get started
                                            </router-link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
}
