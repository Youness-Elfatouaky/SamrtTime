<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/api'

const router = useRouter()
const email = ref('')
const fullName = ref('')
const password = ref('')
const confirmPassword = ref('')
const acceptTerms = ref(false)
const error = ref('')
const isLoading = ref(false)

const passwordStrength = computed(() => {
  if (!password.value) return { score: 0, message: '' }
  
  let score = 0
  const checks = {
    length: password.value.length >= 8,
    lowercase: /[a-z]/.test(password.value),
    uppercase: /[A-Z]/.test(password.value),
    number: /[0-9]/.test(password.value),
    special: /[!@#$%^&*]/.test(password.value)
  }
  
  score = Object.values(checks).filter(Boolean).length
  
  const messages = {
    0: { message: 'Very Weak', color: 'bg-red-500' },
    1: { message: 'Weak', color: 'bg-orange-500' },
    2: { message: 'Fair', color: 'bg-yellow-500' },
    3: { message: 'Good', color: 'bg-blue-500' },
    4: { message: 'Strong', color: 'bg-green-500' },
    5: { message: 'Very Strong', color: 'bg-green-600' }
  }
  
  return {
    score,
    ...messages[score],
    checks
  }
})

const validateForm = () => {
  if (!email.value.trim()) {
    error.value = 'Email is required'
    return false
  }
  if (!fullName.value.trim()) {
    error.value = 'Full name is required'
    return false
  }
  if (!password.value) {
    error.value = 'Password is required'
    return false
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters'
    return false
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return false
  }
  if (passwordStrength.value.score < 3) {
    error.value = 'Please choose a stronger password'
    return false
  }
  if (!acceptTerms.value) {
    error.value = 'You must accept the terms and conditions'
    return false
  }
  return true
}

const handleSubmit = async () => {
  error.value = ''
  if (!validateForm()) return
  
  isLoading.value = true
  try {
    await authService.register({
      email: email.value,
      full_name: fullName.value,
      password: password.value
    })
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <!-- Logo would go here -->
      <div class="w-20 h-20 mx-auto bg-blue-600 rounded-lg flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">Create your account</h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Join SmartTime and start managing your time effectively
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10">
        <form @submit.prevent="handleSubmit" class="space-y-6" novalidate>
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">Email address</label>
            <div class="mt-1">
              <input
                id="email"
                v-model="email"
                type="email"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300': error && !email }"
              />
            </div>
          </div>

          <div>
            <label for="fullName" class="block text-sm font-medium text-gray-700">Full Name</label>
            <div class="mt-1">
              <input
                id="fullName"
                v-model="fullName"
                type="text"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300': error && !fullName }"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
            <div class="mt-1">
              <input
                id="password"
                v-model="password"
                type="password"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300': error && !password }"
              />
            </div>
            <!-- Password Strength Indicator -->
            <div v-if="password" class="mt-2">
              <div class="flex items-center space-x-2">
                <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full transition-all duration-300"
                    :class=" [
                      passwordStrength.color,
                      `w-${passwordStrength.score * 20}%`
                    ] "
                  ></div>
                </div>
                <span class="text-xs font-medium" :class="passwordStrength.color.replace('bg-', 'text-')">
                  {{ passwordStrength.message }}
                </span>
              </div>
              <ul class="mt-2 space-y-1 text-xs text-gray-500">
                <li :class="{ 'text-green-500': passwordStrength.checks.length }">
                  • At least 8 characters
                </li>
                <li :class="{ 'text-green-500': passwordStrength.checks.lowercase && passwordStrength.checks.uppercase }">
                  • Mix of uppercase and lowercase letters
                </li>
                <li :class="{ 'text-green-500': passwordStrength.checks.number }">
                  • At least one number
                </li>
                <li :class="{ 'text-green-500': passwordStrength.checks.special }">
                  • At least one special character (!@#$%^&*)
                </li>
              </ul>
            </div>
          </div>

          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirm Password</label>
            <div class="mt-1">
              <input
                id="confirmPassword"
                v-model="confirmPassword"
                type="password"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{ 'border-red-300': password && confirmPassword && password !== confirmPassword }"
              />
            </div>
            <p v-if="password && confirmPassword && password !== confirmPassword" class="mt-2 text-sm text-red-600">
              Passwords do not match
            </p>
          </div>

          <div class="flex items-start">
            <div class="flex items-center h-5">
              <input
                id="terms"
                v-model="acceptTerms"
                type="checkbox"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            <div class="ml-3 text-sm">
              <label for="terms" class="font-medium text-gray-700">I accept the terms and conditions</label>
              <p class="text-gray-500">By creating an account, you agree to our Terms of Service and Privacy Policy</p>
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
              {{ isLoading ? 'Creating account...' : 'Create account' }}
            </button>
          </div>
        </form>

        <div class="mt-6">
          <div class="relative">
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-white text-gray-500">
                Already have an account?
                <router-link to="/login" class="font-medium text-blue-600 hover:text-blue-500">
                  Sign in
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
</template>

<style scoped>
.w-20\% { width: 20%; }
.w-40\% { width: 40%; }
.w-60\% { width: 60%; }
.w-80\% { width: 80%; }
.w-100\% { width: 100%; }
</style>
