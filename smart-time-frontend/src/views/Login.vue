<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/api'

const router = useRouter()
const login = ref('')
const password = ref('')
const error = ref('')
const rememberMe = ref(false)
const isLoading = ref(false)

const validateForm = () => {
  if (!login.value.trim()) {
    error.value = 'Email or username is required'
    return false
  }
  if (!password.value) {
    error.value = 'Password is required'
    return false
  }
  return true
}

const handleSubmit = async () => {
  error.value = ''
  if (!validateForm()) return

  isLoading.value = true
  try {
    const response = await authService.login({
      login: login.value,
      password: password.value
    })
    const token = response.access_token
    
    // Store token based on remember me preference
    if (rememberMe.value) {
      localStorage.setItem('token', token)
    } else {
      sessionStorage.setItem('token', token)
    }
    
    router.push('/dashboard')
  } catch (err) {
    error.value = 'Invalid credentials. Please check your email/username and password.'
  } finally {
    isLoading.value = false
  }
}

const handleOAuthLogin = (provider) => {
  // This would be implemented when OAuth is added
  console.log(`Login with ${provider}`)
}
</script>

<template>
  <main class="auth-page min-h-screen w-screen overflow-hidden relative bg-gradient-to-br from-indigo-50 via-blue-50 to-purple-50">
    <!-- Background pattern -->
    <div class="absolute inset-0 opacity-30">
      <div class="absolute inset-0 bg-grid-slate-200"></div>
    </div>

    <!-- Content container -->
    <div class="relative min-h-screen w-full flex items-center justify-center px-4">      <div class="w-full max-w-xl">
        <!-- Logo and title section -->
        <div class="text-center mb-8">
          <div class="w-24 h-24 mx-auto bg-blue-600 rounded-2xl flex items-center justify-center shadow-xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 class="mt-6 text-4xl font-extrabold text-gray-900">Welcome to SmartTime</h2>
          <p class="mt-3 text-lg text-gray-600">Your personal time management assistant</p>
        </div>

        <!-- Login form card -->
        <div class="bg-white/80 backdrop-blur-lg shadow-2xl sm:rounded-2xl border border-gray-100">          <div class="px-6 py-10 sm:px-12">
            <form @submit.prevent="handleSubmit" class="space-y-6 max-w-md mx-auto" novalidate>
              <div>
                <label for="login" class="block text-sm font-medium text-gray-700">Email or Username</label>
                <div class="mt-1 relative">
                  <input
                    id="login"
                    v-model="login"
                    type="text"
                    required
                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    :class="{ 'border-red-300': error && !login }"
                  />
                  <div v-if="error && !login" class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>

              <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <div class="mt-1 relative">
                  <input
                    id="password"
                    v-model="password"
                    type="password"
                    required
                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    :class="{ 'border-red-300': error && !password }"
                  />
                  <div v-if="error && !password" class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>

              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <input
                    id="remember-me"
                    v-model="rememberMe"
                    type="checkbox"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label for="remember-me" class="ml-2 block text-sm text-gray-900">
                    Remember me
                  </label>
                </div>

                <div class="text-sm">
                  <a href="#" class="font-medium text-blue-600 hover:text-blue-500">
                    Forgot your password?
                  </a>
                </div>
              </div>

              <div v-if="error" class="rounded-md bg-red-50 p-4">
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <p class="text-sm font-medium text-red-800">{{ error }}</p>
                  </div>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  :disabled="isLoading"
                  class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg
                    v-if="isLoading"
                    class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {{ isLoading ? 'Signing in...' : 'Sign in' }}
                </button>
              </div>
            </form>

            <div class="mt-6">
              <div class="relative">
                <div class="absolute inset-0 flex items-center">
                  <div class="w-full border-t border-gray-300" />
                </div>
                <div class="relative flex justify-center text-sm">
                  <span class="px-2 bg-white text-gray-500">Or continue with</span>
                </div>
              </div>

              <div class="mt-6 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  @click="handleOAuthLogin('google')"
                  class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled
                >
                  <span class="sr-only">Sign in with Google</span>
                  <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/>
                  </svg>
                </button>
                <button
                  type="button"
                  @click="handleOAuthLogin('microsoft')"
                  class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled
                >
                  <span class="sr-only">Sign in with Microsoft</span>
                  <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 23 23">
                    <path fill="#f35325" d="M1 1h10v10H1z"/>
                    <path fill="#81bc06" d="M12 1h10v10H12z"/>
                    <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                    <path fill="#ffba08" d="M12 12h10v10H12z"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="mt-6">
              <div class="relative">
                <div class="relative flex justify-center text-sm">
                  <span class="px-2 bg-white text-gray-500">
                    Don't have an account?
                    <router-link to="/register" class="font-medium text-blue-600 hover:text-blue-500">
                      Register
                    </router-link>
                  </span>
                </div>
              </div>
            </div>

            <div class="mt-6 text-center">
              <div class="space-x-4 text-xs text-gray-500">
                <a href="#" class="hover:text-gray-900">Terms of Service</a>
                <span>•</span>
                <a href="#" class="hover:text-gray-900">Privacy Policy</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.auth-page {
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
}

.bg-grid-slate-200 {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32' fill='none' stroke='rgb(226 232 240 / 0.8)'%3E%3Cpath d='M0 .5H31.5V32'/%3E%3C/svg%3E");
}

@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>
