export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="container mx-auto h-screen">
      {children}
    </div>
  );
}
