'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
    const router = useRouter();
    
    useEffect(() => {
        router.replace('/documents');
    }, [router]);

    return (
        <div style={{ minHeight: '100vh', background: '#0e111b', display: 'flex', alignItems: 'center', justifycontent: 'center', fontFamily: 'system-ui' }}>
            <div style={{ color: '#8899a6', fontSize: '15px' }}>Loading Dashboard...</div>
        </div>
    );
}
