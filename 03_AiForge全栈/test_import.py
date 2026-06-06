try:
    from api.project import router
    print("Router import OK")
    # Check all routes
    for route in router.routes:
        print(f"  {route.methods} {route.path}")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
