import type { ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'
import { cx } from '../lib/utils'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'danger' | 'ghost'
  size?: 'md' | 'sm'
  icon?: boolean
  loading?: boolean
}
export function Button({ variant = 'default', size = 'md', icon, loading, className, children, disabled, type = 'button', ...rest }: Props) {
  return (
    <button
      type={type}
      className={cx('btn', variant !== 'default' && variant, size === 'sm' && 'sm', icon && 'icon', className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Loader2 size={15} className="spin" aria-hidden />}
      {children}
    </button>
  )
}
