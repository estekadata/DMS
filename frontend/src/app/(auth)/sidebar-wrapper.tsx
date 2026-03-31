"use client";

import { Sidebar } from "@/components/sidebar";

interface Props {
  userName: string;
  userRole: string;
}

export function SidebarWrapper({ userName, userRole }: Props) {
  return <Sidebar userName={userName} userRole={userRole} />;
}
