.text
.global _start
_start:
 mov 8(%rdx), %rsi
 test %rsi, %rsi
 jz done
 mov 64(%rsi), %esi
 sub $1417, %esi
 cmp $2, %esi
 jbe matched
 cmp $10, %esi
 je matched
 sub $20, %esi
 cmp $1, %esi
 ja done
matched:
 test %rax, %rax
 jz done
 movl $1000000, 12(%rax)
done:
 mov %rax, 16(%rdx)
 mov %rdx, %rax
 jmp 0x8507b7b
.org 0x60
budget:
 mov %rax, %rcx
 mov $131072, %ebx
 mov $131072, %eax
 jmp 0x8803017
