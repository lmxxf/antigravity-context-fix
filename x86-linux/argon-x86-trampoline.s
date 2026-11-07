.text
.global _start
_start:
 mov 8(%rdx), %rsi
 test %rsi, %rsi
 jz done
 mov 64(%rsi), %esi
 sub $1417, %esi
 cmp $2, %esi
 ja done
 test %rax, %rax
 jz done
 movl $1000000, 12(%rax)
done:
 mov %rax, 16(%rdx)
 mov %rdx, %rax
 jmp 0x82e853b
.org 0x60
budget:
 mov %rax, %rcx
 mov $131072, %ebx
 mov $131072, %eax
 jmp 0x852d977
