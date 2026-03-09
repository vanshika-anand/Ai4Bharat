import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function getPlatformColor(platform: string): string {
  const colors: Record<string, string> = {
    linkedin: 'bg-blue-500',
    twitter: 'bg-sky-400',
    instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
    tiktok: 'bg-black',
    blog: 'bg-green-500',
    general: 'bg-gray-500',
  };
  return colors[platform] || colors.general;
}

export function getPlatformIcon(platform: string): string {
  const icons: Record<string, string> = {
    linkedin: '💼',
    twitter: '🐦',
    instagram: '📸',
    tiktok: '🎵',
    blog: '📝',
    general: '📄',
  };
  return icons[platform] || icons.general;
}
