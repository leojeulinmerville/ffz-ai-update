import Landing from './components/Landing.js';
import Login from './components/Login.js';
import Register from './components/Register.js';
import Dashboard from './components/Dashboard.js';
import Verify from './components/Verify.js';

const { createApp, reactive } = Vue;
const { createRouter, createWebHistory } = VueRouter;

// Simple State Management
const store = reactive({
    user: null,
    token: localStorage.getItem('ffz_token'),
    async fetchUser() {
        if (!this.token) return;
        try {
            const res = await fetch('/auth/me', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            if (res.ok) {
                this.user = await res.json();
            } else {
                this.logout();
            }
        } catch (e) {
            this.logout();
        }
    },
    logout() {
        this.user = null;
        this.token = null;
        localStorage.removeItem('ffz_token');
        router.push('/login');
    }
});

const routes = [
    { path: '/', component: Landing },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/verify', component: Verify },
    { 
        path: '/dashboard', 
        component: Dashboard,
        beforeEnter: (to, from, next) => {
            if (!store.token) next('/login');
            else next();
        }
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

const App = {
    setup() {
        return { store };
    },
    template: `
        <div class="min-h-screen flex flex-col">
            <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between h-16">
                        <div class="flex">
                            <router-link to="/" class="flex-shrink-0 flex items-center font-bold text-xl text-indigo-600">
                                ⚽ FFZ
                            </router-link>
                        </div>
                        <div class="flex items-center space-x-4">
                            <template v-if="store.user">
                                <router-link to="/dashboard" class="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">Dashboard</router-link>
                                <button @click="store.logout()" class="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">Logout</button>
                            </template>
                            <template v-else>
                                <router-link to="/login" class="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">Login</router-link>
                                <router-link to="/register" class="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700">Get Started</router-link>
                            </template>
                        </div>
                    </div>
                </div>
            </nav>
            <main class="flex-grow">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </main>
            <footer class="bg-white border-t border-gray-200 py-8">
                <div class="max-w-7xl mx-auto px-4 text-center text-gray-400 text-sm">
                    &copy; 2025 Football Fan Zone. AI-Powered Weekly Reports.
                </div>
            </footer>
        </div>
    `,
    async mounted() {
        if (store.token) {
            await store.fetchUser();
        }
    }
};

const app = createApp(App);
app.use(router);
app.mount('#app');
